"""ATS port — the Ceipal-shaped interface the recruitment agents depend on.

Maps onto Ceipal ATS v1 resources: Job Postings, Applicants (candidate search),
Submissions, plus RTR/screening write-back (see research/20260630-230003...).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.domain import models as m


class AtsPort(ABC):
    name: str = "ats"

    # --- Jobs (Ceipal Job Postings) ---
    @abstractmethod
    def list_jobs(self, status: str | None = "open") -> list[m.Job]: ...

    @abstractmethod
    def get_job(self, job_id: int) -> m.Job | None: ...

    # --- Candidates (Ceipal Applicants) ---
    @abstractmethod
    def list_candidates(self) -> list[m.Candidate]: ...

    @abstractmethod
    def get_candidate(self, candidate_id: int) -> m.Candidate | None: ...

    @abstractmethod
    def search_candidates(
        self,
        *,
        skills: list[str] | None = None,
        clearance: str | None = None,
        min_years: int = 0,
        location: str | None = None,
        query: str | None = None,
        limit: int = 20,
    ) -> list[m.Candidate]: ...

    # --- Submissions ---
    @abstractmethod
    def create_submission(
        self, *, candidate_id: int, job_id: int, stage: str = "matched",
        rank_score: float = 0.0, rationale: str = "",
    ) -> m.Submission: ...

    @abstractmethod
    def update_submission(self, submission_id: int, **fields: Any) -> m.Submission | None: ...

    # --- RTR / screening write-back ---
    @abstractmethod
    def save_rtr(
        self, *, candidate_id: int, authorized: bool, job_id: int | None = None,
        call_id: int | None = None, client_name: str = "", job_title: str = "",
        pay_rate: str = "", location: str = "", notes: str = "",
    ) -> m.RTR: ...
