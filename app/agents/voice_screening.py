"""HERO: the Recruitment Voice Screening Agent (the brain).

Conducts a phone screen with a candidate for a specific job, then captures a
verbal **Right to Represent (RTR)** and a structured outcome. It is deliberately
**transport-agnostic**: it takes the candidate's words as *text* and returns the
agent's words as *text* plus structured `events`. The websocket layer wires it to
browser speech (client-side STT/TTS) or the local PCM pipeline; the demo script
wires it to a canned LLM. Nothing here knows about audio.

Flow: greeting -> screen (interest, availability, rate, work authorization,
clearance fit, location) -> ask for RTR -> `capture_rtr` -> `end_call` with a
concise outcome + summary. Every turn is persisted as a `TranscriptTurn`, and the
final outcome is written back to the `Call` row and (for the RTR) to the ATS.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.domain import models as m
from app.domain.db import session
from app.integrations.ats.base import AtsPort
from app.llm.base import LLM, Tool, run_tool_loop, user_msg

AGENCY_NAME = "Vantage Federal Staffing"


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


@dataclass
class AgentTurn:
    """One agent response: the words to speak, side-effect events, and whether the
    call is now complete."""

    text: str
    events: list[dict[str, Any]] = field(default_factory=list)
    done: bool = False
    outcome: str = ""


class ScreeningSession:
    """A single live screening conversation for one candidate + job."""

    def __init__(
        self,
        *,
        candidate: m.Candidate,
        job: m.Job,
        llm: LLM,
        ats: AtsPort,
        call_id: int,
        log_turns: bool = True,
    ) -> None:
        self.candidate = candidate
        self.job = job
        self.llm = llm
        self.ats = ats
        self.call_id = call_id
        self.log_turns = log_turns

        self.messages: list[dict[str, Any]] = []
        self.structured: dict[str, Any] = {}
        self.rtr_captured = False
        self.rtr_authorized = False
        self.outcome = ""
        self.summary = ""
        self.done = False
        self._events: list[dict[str, Any]] = []

    # ------------------------------------------------------------------ prompt
    def _system_prompt(self) -> str:
        c, j = self.candidate, self.job
        first = c.name.split()[0]
        return (
            f"You are Alex, a warm, efficient technical recruiter at {AGENCY_NAME}. "
            f"You are on a phone call with {c.name} about a job opening. Conduct a short, "
            "natural phone screen. This is SPOKEN conversation: reply in 1-2 short "
            "sentences, ask ONE thing at a time, never use lists or markdown, and sound human.\n\n"
            "## The role\n"
            f"- Title: {j.title}\n"
            f"- Client: {j.client_name}\n"
            f"- Location: {j.location} ({'remote' if j.remote else 'onsite'})\n"
            f"- Employment: {j.employment_type} | Pay: {j.pay_rate or 'competitive'}\n"
            f"- Clearance required: {j.clearance}\n"
            f"- Key skills: {', '.join(j.skills or []) or 'n/a'}\n"
            f"- Min experience: {j.min_years}+ years\n\n"
            "## The candidate (from our ATS)\n"
            f"- Name: {c.name} (call them {first})\n"
            f"- Current title: {c.current_title} | {c.years_experience} yrs\n"
            f"- Clearance on file: {c.clearance} | Work authorization: {c.work_authorization}\n"
            f"- Location: {c.location} | Desired rate: {c.desired_rate or 'unknown'}\n"
            f"- Skills on file: {', '.join(c.skills or []) or 'n/a'}\n\n"
            "## What to accomplish, in order\n"
            f"1. Confirm you're speaking with {first} and that it's a good moment for a few minutes.\n"
            "2. Pitch the role in ONE sentence (title, client, location, pay).\n"
            "3. Screen briefly and conversationally: confirm interest; availability / notice period; "
            f"desired rate vs the {j.pay_rate or 'listed'} rate; confirm work authorization; and "
            f"confirm clearance fit (role needs {j.clearance}; they have {c.clearance} on file).\n"
            "4. If they're interested and a reasonable fit, ask for a verbal Right to Represent: "
            f"explicit permission to submit them to {j.client_name} for the {j.title} role at "
            f"{j.pay_rate or 'the discussed rate'}. The MOMENT they clearly say yes, call "
            "`capture_rtr` with authorized=true. If they decline representation, call it with "
            "authorized=false.\n"
            "5. When the screen is done (or they're not interested, or it's a bad time), call "
            "`end_call` with a concise outcome, the interested flag, availability, the rate "
            "discussed, and a 1-2 sentence summary. Give a brief friendly sign-off in the same turn.\n\n"
            "Never invent facts beyond what's above. Prefer calling the tools over just promising to."
        )

    # ------------------------------------------------------------------- tools
    def _tools(self) -> list[Tool]:
        return [
            Tool(
                name="capture_rtr",
                description=(
                    "Record the candidate's verbal Right to Represent decision for THIS job. "
                    "Call the instant they clearly authorize (or decline) being submitted to the client."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "authorized": {
                            "type": "boolean",
                            "description": "True if the candidate gave permission to be submitted.",
                        },
                        "notes": {
                            "type": "string",
                            "description": "Short verbatim-ish note of what they agreed to.",
                        },
                    },
                    "required": ["authorized"],
                },
                handler=self._tool_capture_rtr,
            ),
            Tool(
                name="end_call",
                description="Finalize the screen. Call once when the conversation is complete.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "outcome": {
                            "type": "string",
                            "enum": [
                                "rtr_collected",
                                "interested",
                                "not_interested",
                                "callback",
                                "not_a_fit",
                            ],
                            "description": "Best single label for how the call ended.",
                        },
                        "interested": {"type": "boolean"},
                        "availability": {"type": "string"},
                        "pay_rate": {"type": "string", "description": "Rate the candidate wants / agreed."},
                        "summary": {"type": "string", "description": "1-2 sentence recap for the recruiter."},
                        "notes": {"type": "string"},
                    },
                    "required": ["outcome", "summary"],
                },
                handler=self._tool_end_call,
            ),
        ]

    def _tool_capture_rtr(self, args: dict[str, Any]) -> dict[str, Any]:
        authorized = bool(args.get("authorized"))
        rtr = self.ats.save_rtr(
            candidate_id=self.candidate.id,
            authorized=authorized,
            job_id=self.job.id,
            call_id=self.call_id,
            client_name=self.job.client_name,
            job_title=self.job.title,
            pay_rate=self.job.pay_rate,
            location=self.job.location,
            notes=str(args.get("notes", "")),
        )
        self.rtr_captured = True
        self.rtr_authorized = authorized
        self._events.append(
            {"event": "rtr_captured", "authorized": authorized, "rtr_id": rtr.id}
        )
        return {"ok": True, "rtr_id": rtr.id, "authorized": authorized}

    def _tool_end_call(self, args: dict[str, Any]) -> dict[str, Any]:
        self.structured.update(
            {
                "interested": bool(args.get("interested", self.rtr_authorized)),
                "availability": args.get("availability", ""),
                "pay_rate": args.get("pay_rate", ""),
                "notes": args.get("notes", ""),
                "rtr_authorized": self.rtr_authorized if self.rtr_captured else None,
            }
        )
        self.outcome = args.get("outcome") or (
            "rtr_collected" if self.rtr_authorized else "completed"
        )
        self.summary = str(args.get("summary", ""))
        self.done = True
        self._events.append({"event": "call_ended", "outcome": self.outcome})
        return {"ok": True}

    # -------------------------------------------------------------- transcript
    def _record_turn(self, role: str, text: str) -> None:
        if not (self.log_turns and text):
            return
        with session() as s:
            s.add(m.TranscriptTurn(call_id=self.call_id, role=role, text=text))
            s.commit()

    # --------------------------------------------------------------- lifecycle
    def greeting(self) -> str:
        """Deterministic, low-latency opening line (no model round-trip)."""
        first = self.candidate.name.split()[0]
        text = (
            f"Hi, may I speak with {first}? This is Alex calling from {AGENCY_NAME} "
            f"about a {self.job.title} opportunity — is now an okay time for a few minutes?"
        )
        self.messages.append({"role": "assistant", "content": text, "tool_calls": []})
        self._record_turn("agent", text)
        return text

    def user_says(self, text: str) -> AgentTurn:
        """Feed one candidate utterance; return the agent's spoken reply + events."""
        if self.done:
            return AgentTurn(text="", done=True, outcome=self.outcome)

        self._record_turn("human", text)
        self.messages.append(user_msg(text))
        self._events = []

        reply = run_tool_loop(
            self.llm,
            system=self._system_prompt(),
            messages=self.messages,
            tools=self._tools(),
            max_steps=5,
            max_tokens=400,
            temperature=0.4,
        )

        self._record_turn("agent", reply.text)
        turn = AgentTurn(
            text=reply.text,
            events=list(self._events),
            done=self.done,
            outcome=self.outcome,
        )
        return turn

    def finalize(self) -> None:
        """Write the outcome/summary/structured data back onto the Call row."""
        with session() as s:
            call = s.get(m.Call, self.call_id)
            if not call:
                return
            call.status = "completed"
            call.outcome = self.outcome or ("rtr_collected" if self.rtr_authorized else "completed")
            call.summary = self.summary
            call.structured = self.structured
            call.ended_at = _now()
            s.add(call)
            s.commit()


def create_call(candidate_id: int, job_id: int, *, direction: str = "outbound") -> m.Call:
    """Open a new screening `Call` row and return it (detached, id populated)."""
    with session() as s:
        call = m.Call(
            direction=direction,
            agent_type="voice_screening",
            party_type="candidate",
            party_id=candidate_id,
            job_id=job_id,
            status="in_progress",
        )
        s.add(call)
        s.commit()
        s.refresh(call)
        return call
