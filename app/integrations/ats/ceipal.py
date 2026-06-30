"""Real Ceipal ATS adapter (stub).

Ceipal has no free tier (the portal is gated), so this stays a stub unless the
owner supplies sandbox creds. Plan (see research/20260630-230003...):
  * Auth with email + password + api_key -> access token; renew via Refresh Token.
  * Map: search_candidates -> Applicants, list_jobs -> Job Postings,
    create_submission -> Submissions, save_rtr -> screening write-back.
"""

from __future__ import annotations

from app.config import Settings
from app.integrations.ats.base import AtsPort


class CeipalAts(AtsPort):
    name = "ceipal"

    def __init__(self, settings: Settings):
        self.settings = settings

    def _not_ready(self, *_a, **_k):
        raise NotImplementedError(
            "Real Ceipal adapter is a stub — set USE_MOCKS=true to use MockCeipalAts, "
            "or implement the v1 calls per research/20260630-230003..."
        )

    list_jobs = get_job = list_candidates = get_candidate = _not_ready
    search_candidates = create_submission = update_submission = save_rtr = _not_ready
