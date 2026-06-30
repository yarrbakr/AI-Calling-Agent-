"""Real SMTP email adapter (stub for now; trivial to finish in Phase 5).

Sends for free via any SMTP server (e.g. Gmail App Password). Selected only when
USE_MOCKS=false and SMTP_* is configured.
"""

from __future__ import annotations

from app.config import Settings
from app.integrations.email.base import EmailPort


class SmtpEmail(EmailPort):
    name = "smtp_email"

    def __init__(self, settings: Settings):
        self.settings = settings

    def send_email(self, *, to, subject, body, about_type="", about_id=None):
        raise NotImplementedError(
            "Real SMTP email is a stub — set USE_MOCKS=true to use MockEmail, "
            "or implement smtplib.SMTP send in Phase 5."
        )
