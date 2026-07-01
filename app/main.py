"""FastAPI application entrypoint.

Serves the live screening dashboard + call websocket (Phase 2) alongside health
and stats. Static assets and the dashboard template live under ``app/web``.

Run (from the project root, via the shared venv):
    ../.venv/Scripts/python.exe -m uvicorn app.main:app --reload
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select

from app.config import settings
from app.domain import models as m
from app.domain.db import engine, init_db
from app.integrations.factory import get_ats, get_crm, get_email, get_messaging
from app.speech.factory import get_speech
from app.web.routes import router as web_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="P1 AI Calling Agent", version="0.1.0", lifespan=lifespan)

app.mount(
    "/static",
    StaticFiles(directory=str(Path(__file__).parent / "web" / "static")),
    name="static",
)
app.include_router(web_router)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "use_mocks": settings.use_mocks,
        "llm_backend_setting": settings.llm_backend,
        "llm_backend_active": settings.active_llm_backend(),
        "speech_mode": settings.speech_mode,
        "speech_engine": get_speech().name,
        "adapters": {
            "crm": get_crm().name,
            "ats": get_ats().name,
            "messaging": get_messaging().name,
            "email": get_email().name,
        },
    }


@app.get("/api/stats")
def stats() -> dict:
    with Session(engine) as s:
        def count(model) -> int:
            return len(s.exec(select(model)).all())

        return {
            "clients": count(m.Client),
            "leads": count(m.Lead),
            "jobs": count(m.Job),
            "candidates": count(m.Candidate),
            "contacts": count(m.Contact),
            "calls": count(m.Call),
        }
