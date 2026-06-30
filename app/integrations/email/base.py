"""Email port. Mock writes to a data/outbox file; real SMTP sends for free."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain import models as m


class EmailPort(ABC):
    name: str = "email"

    @abstractmethod
    def send_email(
        self, *, to: str, subject: str, body: str,
        about_type: str = "", about_id: int | None = None,
    ) -> m.Message: ...
