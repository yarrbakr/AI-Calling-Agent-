"""Real Zoho CRM adapter (stub).

Wired in a later phase. Selected only when USE_MOCKS=false and ZOHO_* creds are set.
Implementation plan (see research/20260630-230002...):
  * OAuth self-client: refresh the access token via
    POST https://accounts.zoho.com/oauth/v2/token (grant_type=refresh_token).
  * Map: create_lead -> POST /crm/v2/Leads, log_call -> /crm/v2/Calls,
    schedule_meeting -> /crm/v2/Events, create_contact -> /crm/v2/Contacts.
"""

from __future__ import annotations

from app.config import Settings
from app.integrations.crm.base import CrmPort


class ZohoCrm(CrmPort):
    name = "zoho"

    def __init__(self, settings: Settings):
        self.settings = settings
        self._access_token: str | None = None

    def _not_ready(self, *_a, **_k):
        raise NotImplementedError(
            "Real Zoho adapter is a stub — set USE_MOCKS=true to use MockZohoCrm, "
            "or implement the /crm/v2 calls per research/20260630-230002..."
        )

    # All port methods are stubbed until the real integration phase.
    list_leads = get_lead = create_lead = update_lead = _not_ready
    list_clients = get_client = create_contact = _not_ready
    log_call = schedule_meeting = create_task = _not_ready
