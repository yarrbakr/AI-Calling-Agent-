"""Real Vonage messaging adapter (stub).

Targets the Vonage Messages API; WhatsApp via the free sandbox (no business approval
needed) — see research/20260630-230006... Wired in Phase 5.
"""

from __future__ import annotations

from app.config import Settings
from app.integrations.messaging.base import MessagingPort


class VonageMessaging(MessagingPort):
    name = "vonage_messaging"

    def __init__(self, settings: Settings):
        self.settings = settings

    def _not_ready(self, *_a, **_k):
        raise NotImplementedError(
            "Real Vonage messaging is a stub — set USE_MOCKS=true to use MockMessaging, "
            "or implement the Messages API per research/20260630-230006..."
        )

    send_sms = send_whatsapp = _not_ready
