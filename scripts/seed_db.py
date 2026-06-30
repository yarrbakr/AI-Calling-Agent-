"""Seed the SQLite store from data/seed/*.json.

Idempotent: wipes the domain tables and reloads them, so you always get a known
demo dataset. Run via the shared venv:

    ../.venv/Scripts/python.exe scripts/seed_db.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow running as a plain script (add project root to import path).
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlmodel import Session, select  # noqa: E402

from app.config import SEED_DIR  # noqa: E402
from app.domain import models as m  # noqa: E402
from app.domain.db import engine, init_db  # noqa: E402

# Wipe order respects foreign keys (children first).
_WIPE_ORDER = (
    m.SurveyResponse, m.Task, m.Message, m.RTR, m.TranscriptTurn, m.Call,
    m.Submission, m.Meeting, m.Contact, m.Candidate, m.Job, m.Lead, m.Client,
)


def _load(name: str) -> list[dict]:
    with open(SEED_DIR / name, encoding="utf-8") as f:
        return json.load(f)


def seed(reset: bool = True) -> dict[str, int]:
    init_db()
    with Session(engine) as s:
        if reset:
            for model in _WIPE_ORDER:
                for obj in s.exec(select(model)).all():
                    s.delete(obj)
            s.commit()

        # Clients first so jobs/contacts can resolve client_name -> client_id.
        clients: dict[str, int] = {}
        for row in _load("clients.json"):
            c = m.Client(**row)
            s.add(c)
            s.commit()
            s.refresh(c)
            clients[c.name] = c.id

        for row in _load("jobs.json"):
            s.add(m.Job(client_id=clients.get(row.get("client_name")), **row))

        for row in _load("contacts.json"):
            cname = row.pop("client_name", None)
            s.add(m.Contact(client_id=clients.get(cname), **row))

        for row in _load("candidates.json"):
            s.add(m.Candidate(**row))

        for row in _load("leads.json"):
            s.add(m.Lead(**row))

        s.commit()

        counts = {
            "clients": len(s.exec(select(m.Client)).all()),
            "jobs": len(s.exec(select(m.Job)).all()),
            "contacts": len(s.exec(select(m.Contact)).all()),
            "candidates": len(s.exec(select(m.Candidate)).all()),
            "leads": len(s.exec(select(m.Lead)).all()),
        }
    return counts


if __name__ == "__main__":
    print("Seeding database ...")
    result = seed(reset=True)
    for k, v in result.items():
        print(f"  {k:12} {v}")
    print("Done.")
