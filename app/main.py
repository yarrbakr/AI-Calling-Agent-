"""FastAPI application entrypoint.

For now this exposes health + stats and a placeholder home page so we can verify
the foundation boots. The live dashboard and call websocket arrive in Phase 2.

Run (from the project root, via the shared venv):
    ../.venv/Scripts/python.exe -m uvicorn app.main:app --reload
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select

from app.config import settings
from app.domain import models as m
from app.domain.db import engine, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="P1 AI Calling Agent", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "use_mocks": settings.use_mocks,
        "llm_backend_setting": settings.llm_backend,
        "llm_backend_active": settings.active_llm_backend(),
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


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return (
        "<html><body style='font-family:system-ui;max-width:640px;margin:3rem auto'>"
        "<h1>P1 — AI Calling Agent</h1>"
        "<p>Foundation is up. CRM/ATS store, config, and mock switches are live.</p>"
        "<ul>"
        "<li><a href='/health'>/health</a></li>"
        "<li><a href='/api/stats'>/api/stats</a></li>"
        "<li><a href='/docs'>/docs</a> (OpenAPI)</li>"
        "</ul>"
        "<p>The live screening-call dashboard arrives in Phase 2.</p>"
        "</body></html>"
    )
