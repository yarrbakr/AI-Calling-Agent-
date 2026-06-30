"""Mock messaging — records SMS/WhatsApp to the DB + a data/outbox file ($0)."""

from __future__ import annotations

from app.config import OUTBOX_DIR
from app.domain import models as m
from app.domain.db import session
from app.integrations.messaging.base import MessagingPort


class MockMessaging(MessagingPort):
    name = "mock_messaging"

    def _send(self, channel: str, to: str, body: str, about_type: str, about_id: int | None) -> m.Message:
        OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
        with session() as s:
            msg = m.Message(
                channel=channel, to_addr=to, body=body, status="sent",
                about_type=about_type, about_id=about_id, provider="mock",
            )
            s.add(msg)
            s.commit()
            s.refresh(msg)
        (OUTBOX_DIR / f"{channel}_{msg.id}.txt").write_text(
            f"To: {to}\nChannel: {channel}\n\n{body}\n", encoding="utf-8"
        )
        return msg

    def send_sms(self, *, to: str, body: str, about_type: str = "", about_id: int | None = None) -> m.Message:
        return self._send("sms", to, body, about_type, about_id)

    def send_whatsapp(self, *, to: str, body: str, about_type: str = "", about_id: int | None = None) -> m.Message:
        return self._send("whatsapp", to, body, about_type, about_id)
