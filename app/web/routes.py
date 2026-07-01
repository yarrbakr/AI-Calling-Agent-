"""Dashboard page, JSON endpoints, and the live call websocket.

Browser speech mode (default): the websocket carries **text** turns. The client
does mic capture, STT, TTS and barge-in with the Web Speech API; the server runs
the screening brain and streams back the agent's words + structured events. The
same protocol is reused by the local PCM pipeline later (the client just sends
transcribed text either way).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, desc, select
from starlette.concurrency import run_in_threadpool

from app.agents.voice_screening import ScreeningSession, create_call
from app.config import settings
from app.domain import models as m
from app.domain.db import engine
from app.integrations.factory import get_ats
from app.llm.factory import get_llm

router = APIRouter()

_TEMPLATES = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


# --------------------------------------------------------------------------- #
# Serializers
# --------------------------------------------------------------------------- #
def _candidate_dict(c: m.Candidate) -> dict[str, Any]:
    return {
        "id": c.id,
        "name": c.name,
        "current_title": c.current_title,
        "clearance": c.clearance,
        "years_experience": c.years_experience,
        "skills": c.skills or [],
        "location": c.location,
    }


def _job_dict(j: m.Job) -> dict[str, Any]:
    return {
        "id": j.id,
        "title": j.title,
        "client_name": j.client_name,
        "location": j.location,
        "clearance": j.clearance,
        "pay_rate": j.pay_rate,
        "skills": j.skills or [],
    }


def _call_dict(c: m.Call, *, party_name: str = "", job_title: str = "") -> dict[str, Any]:
    return {
        "id": c.id,
        "party_name": party_name,
        "job_title": job_title,
        "status": c.status,
        "outcome": c.outcome,
        "summary": c.summary,
        "structured": c.structured or {},
        "started_at": c.started_at.isoformat() if c.started_at else None,
    }


# --------------------------------------------------------------------------- #
# Pages + JSON
# --------------------------------------------------------------------------- #
@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request) -> HTMLResponse:
    ats = get_ats()
    candidates = [_candidate_dict(c) for c in ats.list_candidates()]
    jobs = [_job_dict(j) for j in ats.list_jobs(status="open")]
    return _TEMPLATES.TemplateResponse(
        request,
        "dashboard.html",
        {
            "candidates": candidates,
            "jobs": jobs,
            "speech_mode": settings.speech_mode,
            "llm_backend": settings.active_llm_backend(),
        },
    )


@router.get("/api/calls")
def recent_calls(limit: int = 15) -> list[dict[str, Any]]:
    with Session(engine) as s:
        calls = list(s.exec(select(m.Call).order_by(desc(m.Call.id)).limit(limit)).all())
        cand_names = {c.id: c.name for c in s.exec(select(m.Candidate)).all()}
        job_titles = {j.id: j.title for j in s.exec(select(m.Job)).all()}
    return [
        _call_dict(
            c,
            party_name=cand_names.get(c.party_id or -1, ""),
            job_title=job_titles.get(c.job_id or -1, ""),
        )
        for c in calls
    ]


@router.get("/api/calls/{call_id}")
def call_detail(call_id: int) -> dict[str, Any]:
    with Session(engine) as s:
        call = s.get(m.Call, call_id)
        if not call:
            return {"error": "not found"}
        turns = list(
            s.exec(select(m.TranscriptTurn).where(m.TranscriptTurn.call_id == call_id)).all()
        )
        rtrs = list(s.exec(select(m.RTR).where(m.RTR.call_id == call_id)).all())
        cand = s.get(m.Candidate, call.party_id) if call.party_id else None
        job = s.get(m.Job, call.job_id) if call.job_id else None
    return {
        **_call_dict(
            call,
            party_name=cand.name if cand else "",
            job_title=job.title if job else "",
        ),
        "transcript": [{"role": t.role, "text": t.text} for t in turns],
        "rtr": [
            {"authorized": r.authorized, "job_title": r.job_title, "notes": r.notes}
            for r in rtrs
        ],
    }


# --------------------------------------------------------------------------- #
# Live call websocket (browser text protocol)
# --------------------------------------------------------------------------- #
@router.websocket("/ws/call")
async def call_ws(ws: WebSocket) -> None:
    await ws.accept()
    sess: ScreeningSession | None = None
    try:
        while True:
            msg = await ws.receive_json()
            kind = msg.get("type")

            if kind == "start":
                ats = get_ats()
                cand = ats.get_candidate(int(msg["candidate_id"]))
                job = ats.get_job(int(msg["job_id"]))
                if not cand or not job:
                    await ws.send_json({"type": "error", "error": "unknown candidate or job"})
                    continue
                call = create_call(cand.id, job.id)
                sess = ScreeningSession(
                    candidate=cand,
                    job=job,
                    llm=get_llm(realtime=True),
                    ats=ats,
                    call_id=call.id,
                )
                await ws.send_json(
                    {
                        "type": "ready",
                        "call_id": call.id,
                        "candidate": _candidate_dict(cand),
                        "job": _job_dict(job),
                        "speech_mode": settings.speech_mode,
                    }
                )
                await ws.send_json({"type": "agent", "text": sess.greeting(), "speak": True})

            elif kind == "user":
                if sess is None:
                    await ws.send_json({"type": "error", "error": "call not started"})
                    continue
                text = (msg.get("text") or "").strip()
                if not text:
                    continue
                try:
                    turn = await run_in_threadpool(sess.user_says, text)
                except Exception as exc:  # a transient LLM error shouldn't drop the call
                    await ws.send_json(
                        {
                            "type": "agent",
                            "text": "Sorry, could you say that again?",
                            "speak": True,
                        }
                    )
                    await ws.send_json({"type": "event", "event": "brain_error", "detail": str(exc)})
                    continue
                await ws.send_json({"type": "agent", "text": turn.text, "speak": True})
                for ev in turn.events:
                    await ws.send_json({"type": "event", **ev})
                if turn.done:
                    sess.finalize()
                    await ws.send_json(
                        {
                            "type": "end",
                            "outcome": sess.outcome,
                            "summary": sess.summary,
                            "structured": sess.structured,
                        }
                    )

            elif kind == "hangup":
                if sess is not None and not sess.done:
                    sess.finalize()
                await ws.send_json({"type": "end", "outcome": sess.outcome if sess else "aborted"})
                break

    except WebSocketDisconnect:
        if sess is not None and not sess.done:
            sess.finalize()
