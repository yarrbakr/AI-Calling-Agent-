"""Resolve which adapter each port uses, based on config.

Default (USE_MOCKS=true) -> Mock everywhere ($0, offline). Flip USE_MOCKS=false and
provide a service's creds to switch just that port to its real adapter.
"""

from __future__ import annotations

from app.config import Settings
from app.config import settings as _default_settings
from app.integrations.ats.base import AtsPort
from app.integrations.crm.base import CrmPort
from app.integrations.email.base import EmailPort
from app.integrations.messaging.base import MessagingPort


def get_crm(settings: Settings | None = None) -> CrmPort:
    s = settings or _default_settings
    if s.crm_is_real():
        from app.integrations.crm.zoho import ZohoCrm

        return ZohoCrm(s)
    from app.integrations.crm.mock_zoho import MockZohoCrm

    return MockZohoCrm()


def get_ats(settings: Settings | None = None) -> AtsPort:
    s = settings or _default_settings
    if s.ats_is_real():
        from app.integrations.ats.ceipal import CeipalAts

        return CeipalAts(s)
    from app.integrations.ats.mock_ceipal import MockCeipalAts

    return MockCeipalAts()


def get_messaging(settings: Settings | None = None) -> MessagingPort:
    s = settings or _default_settings
    if not s.use_mocks and s.vonage_application_id:
        from app.integrations.messaging.vonage import VonageMessaging

        return VonageMessaging(s)
    from app.integrations.messaging.mock import MockMessaging

    return MockMessaging()


def get_email(settings: Settings | None = None) -> EmailPort:
    s = settings or _default_settings
    if s.email_is_real():
        from app.integrations.email.smtp import SmtpEmail

        return SmtpEmail(s)
    from app.integrations.email.mock import MockEmail

    return MockEmail()
