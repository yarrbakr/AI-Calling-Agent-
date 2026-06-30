"""Mock email — writes an .eml-style file to data/outbox + a Message row ($0)."""

from __future__ import annotations

from app.config import OUTBOX_DIR, settings
from app.domain import models as m
from app.domain.db import session
from app.integrations.email.base import EmailPort


class MockEmail(EmailPort):
    name = "mock_email"

    def send_email(
        self, *, to: str, subject: str, body: str,
        about_type: str = "", about_id: int | None = None,
    ) -> m.Message:
        OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
        with session() as s:
            msg = m.Message(
                channel="email", to_addr=to, subject=subject, body=body, status="sent",
                about_type=about_type, about_id=about_id, provider="mock",
            )
            s.add(msg)
            s.commit()
            s.refresh(msg)
        eml = f"From: {settings.smtp_from}\nTo: {to}\nSubject: {subject}\n\n{body}\n"
        (OUTBOX_DIR / f"email_{msg.id}.eml").write_text(eml, encoding="utf-8")
        return msg
