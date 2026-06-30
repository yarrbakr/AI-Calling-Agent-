"""Messaging port — SMS + WhatsApp for multi-channel follow-ups.

Mock logs to the Message table + a data/outbox file ($0). The real Vonage adapter
targets the Messages API (WhatsApp via the free sandbox) — see
research/20260630-230006...
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain import models as m


class MessagingPort(ABC):
    name: str = "messaging"

    @abstractmethod
    def send_sms(self, *, to: str, body: str, about_type: str = "", about_id: int | None = None) -> m.Message: ...

    @abstractmethod
    def send_whatsapp(self, *, to: str, body: str, about_type: str = "", about_id: int | None = None) -> m.Message: ...
