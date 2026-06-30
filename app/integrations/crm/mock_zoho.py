"""Mock Zoho CRM — the default, $0 adapter backed by SQLite.

Behaves like Zoho's system of record (create/read leads, contacts, log calls, book
meetings, create tasks) so the agents and dashboard work with no cloud account.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlmodel import select

from app.domain import models as m
from app.domain.db import session
from app.integrations.crm.base import CrmPort


class MockZohoCrm(CrmPort):
    name = "mock_zoho"

    def list_leads(self, status: str | None = None) -> list[m.Lead]:
        with session() as s:
            stmt = select(m.Lead)
            if status:
                stmt = stmt.where(m.Lead.status == status)
            return list(s.exec(stmt).all())

    def get_lead(self, lead_id: int) -> m.Lead | None:
        with session() as s:
            return s.get(m.Lead, lead_id)

    def create_lead(self, **fields: Any) -> m.Lead:
        with session() as s:
            lead = m.Lead(**fields)
            s.add(lead)
            s.commit()
            s.refresh(lead)
            return lead

    def update_lead(self, lead_id: int, **fields: Any) -> m.Lead | None:
        with session() as s:
            lead = s.get(m.Lead, lead_id)
            if not lead:
                return None
            for k, v in fields.items():
                setattr(lead, k, v)
            s.add(lead)
            s.commit()
            s.refresh(lead)
            return lead

    def list_clients(self) -> list[m.Client]:
        with session() as s:
            return list(s.exec(select(m.Client)).all())

    def get_client(self, client_id: int) -> m.Client | None:
        with session() as s:
            return s.get(m.Client, client_id)

    def create_contact(self, **fields: Any) -> m.Contact:
        with session() as s:
            contact = m.Contact(**fields)
            s.add(contact)
            s.commit()
            s.refresh(contact)
            return contact

    def log_call(self, **fields: Any) -> m.Call:
        with session() as s:
            call = m.Call(**fields)
            s.add(call)
            s.commit()
            s.refresh(call)
            return call

    def schedule_meeting(self, *, scheduled_for: datetime, **fields: Any) -> m.Meeting:
        with session() as s:
            meeting = m.Meeting(scheduled_for=scheduled_for, **fields)
            s.add(meeting)
            s.commit()
            s.refresh(meeting)
            return meeting

    def create_task(self, **fields: Any) -> m.Task:
        with session() as s:
            task = m.Task(**fields)
            s.add(task)
            s.commit()
            s.refresh(task)
            return task
