"""Headless, deterministic $0 demo of the HERO Voice Screening Agent.

Drives a full screening conversation with the **canned** LLM (no API key, no
network, no browser, no mic) so the whole pipeline — screening flow, RTR capture,
transcript logging, outcome write-back — is provable in CI and offline.

Scenario: screen **Priya Sharma** (active Secret, senior Java) for the **Senior
Java Developer** role, ending in a captured Right to Represent.

Run via the shared venv:
    ../.venv/Scripts/python.exe scripts/demo_call.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Print UTF-8 regardless of the Windows console code page (cp1252 can't encode ✓).
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlmodel import select  # noqa: E402

from app.agents.voice_screening import ScreeningSession, create_call  # noqa: E402
from app.domain import models as m  # noqa: E402
from app.domain.db import init_db, session  # noqa: E402
from app.integrations.factory import get_ats  # noqa: E402
from app.llm.base import LLMReply, ToolCall  # noqa: E402
from app.llm.canned import CannedLLM  # noqa: E402

# --- What the (simulated) candidate says, turn by turn --------------------- #
USER_TURNS = [
    "Hi, yes, this is Priya. Sure, I have a few minutes.",
    "Yes, I'm interested — tell me more about it.",
    "I could start in about two weeks.",
    "Yes, seventy-five an hour on C2C works for me.",
    "Correct — I'm a US citizen with an active Secret clearance.",
    "Yes, you have my permission to represent me for this role.",
]

# --- What the canned "brain" returns, in complete() call order ------------- #
# Turns 1-5 => one reply each. The final turn drives capture_rtr -> end_call ->
# a spoken sign-off (three complete() calls), mirroring a real tool-use loop.
SCRIPT = [
    LLMReply(text=(
        "Great, thanks Priya! I'm calling about a Senior Java Developer role with "
        "Federal Systems Integrators in Washington, DC — it's C2C around seventy-five "
        "an hour. Is that something you'd be open to hearing about?"
    )),
    LLMReply(text=(
        "Awesome. You'd be building and modernizing Spring Boot microservices on AWS "
        "for a DoD case-management platform. To start — are you available soon, or do "
        "you have a notice period?"
    )),
    LLMReply(text=(
        "Perfect. And the role pays about seventy-five an hour on C2C — does that line "
        "up with what you're looking for?"
    )),
    LLMReply(text=(
        "Great. Just to confirm two compliance items — you're a US citizen with an "
        "active Secret clearance, is that right?"
    )),
    LLMReply(text=(
        "Excellent, you're a strong fit. Do I have your permission to represent you and "
        "submit your profile to Federal Systems Integrators for this Senior Java "
        "Developer role at seventy-five an hour, C2C?"
    )),
    # Candidate says yes -> capture RTR:
    LLMReply(tool_calls=[ToolCall(
        id="rtr-1",
        name="capture_rtr",
        arguments={
            "authorized": True,
            "notes": "Verbally authorized submission to Federal Systems Integrators "
                     "for Senior Java Developer at $75/hr C2C.",
        },
    )]),
    # then finalize the call:
    LLMReply(tool_calls=[ToolCall(
        id="end-1",
        name="end_call",
        arguments={
            "outcome": "rtr_collected",
            "interested": True,
            "availability": "~2 weeks",
            "pay_rate": "$75/hr C2C",
            "summary": "Priya confirmed interest, ~2 week availability, $75/hr C2C, US "
                       "citizen with active Secret. Authorized RTR for the Senior Java "
                       "Developer role.",
        },
    )]),
    # then the spoken sign-off:
    LLMReply(text=(
        "Wonderful — thank you, Priya! I've recorded your authorization and I'll submit "
        "you today. You'll hear from us with next steps. Have a great day!"
    )),
]


def _find(items, name_part, default_id=1):
    for it in items:
        title = getattr(it, "name", None) or getattr(it, "title", "")
        if name_part.lower() in title.lower():
            return it
    return items[default_id - 1] if items else None


def main() -> int:
    init_db()
    ats = get_ats()

    if not ats.list_candidates():
        from scripts.seed_db import seed

        print("Seeding demo data ...")
        seed(reset=True)

    candidate = _find(ats.list_candidates(), "Priya")
    job = _find(ats.list_jobs(status="open"), "Senior Java")
    if not candidate or not job:
        print("!! Could not resolve the demo candidate/job. Run scripts/seed_db.py first.")
        return 1

    call = create_call(candidate.id, job.id)
    llm = CannedLLM(script=SCRIPT)
    sess = ScreeningSession(candidate=candidate, job=job, llm=llm, ats=ats, call_id=call.id)

    print("=" * 74)
    print(f"  HERO DEMO — Voice Screening (canned LLM, $0)   call #{call.id}")
    print(f"  Candidate: {candidate.name} ({candidate.clearance})")
    print(f"  Job:       {job.title} @ {job.client_name} — needs {job.clearance}")
    print("=" * 74)

    print(f"\nAgent · Alex: {sess.greeting()}")
    for line in USER_TURNS:
        print(f"\nCandidate:   {line}")
        turn = sess.user_says(line)
        if turn.text:
            print(f"Agent · Alex: {turn.text}")
        for ev in turn.events:
            print(f"   [event] {ev}")
        if turn.done:
            break

    sess.finalize()

    print("\n" + "-" * 74)
    print("OUTCOME")
    print("-" * 74)
    with session() as s:
        final = s.get(m.Call, call.id)
        print(f"  status   : {final.status}")
        print(f"  outcome  : {final.outcome}")
        print(f"  summary  : {final.summary}")
        print(f"  structured: {final.structured}")
        turns = s.exec(
            select(m.TranscriptTurn).where(m.TranscriptTurn.call_id == call.id)
        ).all()
        rtrs = s.exec(select(m.RTR).where(m.RTR.call_id == call.id)).all()
        print(f"  transcript turns logged: {len(turns)}")
        for r in rtrs:
            flag = "AUTHORIZED" if r.authorized else "DECLINED"
            print(f"  RTR #{r.id}: {flag} — {r.job_title} @ {r.client_name} ({r.pay_rate})")

    ok = bool(rtrs) and final.outcome == "rtr_collected"
    print("\n" + ("PASS ✓  RTR captured and outcome recorded." if ok else "FAIL ✗"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
