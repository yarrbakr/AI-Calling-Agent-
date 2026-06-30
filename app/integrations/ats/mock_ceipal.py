"""Mock Ceipal ATS — default, $0 adapter backed by SQLite.

Implements job/candidate reads, a skills+clearance+experience matching score (reused
by the recruitment agents in Phase 3), submissions, and RTR write-back.
"""

from __future__ import annotations

from typing import Any

from sqlmodel import select

from app.domain import models as m
from app.domain.db import session
from app.integrations.ats.base import AtsPort

# Clearance hierarchy for "candidate meets requirement" checks.
CLEARANCE_RANK = {"none": 0, "public trust": 1, "secret": 2, "top secret": 3, "ts/sci": 4}


def _clr(value: str | None) -> int:
    return CLEARANCE_RANK.get((value or "none").strip().lower(), 0)


def score_candidate(
    cand: m.Candidate,
    *,
    skills: list[str] | None = None,
    min_years: int = 0,
    clearance: str | None = None,
) -> tuple[float, str]:
    """Return a 0-100 match score and a short human rationale.

    Weighting: skills 60, experience 20, clearance 20 (with neutral credit when a
    dimension isn't specified). A clearance shortfall is flagged, not hard-failed.
    """
    req = [s.lower() for s in (skills or [])]
    have = [s.lower() for s in (cand.skills or [])]
    notes: list[str] = []
    score = 0.0

    if req:
        matched = [s for s in req if s in have]
        score += 60 * (len(matched) / len(req))
        notes.append(f"skills {len(matched)}/{len(req)}" + (f" ({', '.join(matched)})" if matched else ""))
    else:
        score += 30

    if min_years:
        if cand.years_experience >= min_years:
            score += 20
            notes.append(f"{cand.years_experience}y exp meets {min_years}+")
        else:
            score += 20 * (cand.years_experience / min_years)
            notes.append(f"{cand.years_experience}y exp under {min_years}")
    else:
        score += 10

    if clearance and _clr(clearance) > 0:
        if _clr(cand.clearance) >= _clr(clearance):
            score += 20
            notes.append(f"clearance {cand.clearance} meets {clearance}")
        else:
            notes.append(f"CLEARANCE GAP: has {cand.clearance}, needs {clearance}")
    else:
        score += 10

    return round(min(score, 100.0), 1), "; ".join(notes)


class MockCeipalAts(AtsPort):
    name = "mock_ceipal"

    def list_jobs(self, status: str | None = "open") -> list[m.Job]:
        with session() as s:
            stmt = select(m.Job)
            if status:
                stmt = stmt.where(m.Job.status == status)
            return list(s.exec(stmt).all())

    def get_job(self, job_id: int) -> m.Job | None:
        with session() as s:
            return s.get(m.Job, job_id)

    def list_candidates(self) -> list[m.Candidate]:
        with session() as s:
            return list(s.exec(select(m.Candidate)).all())

    def get_candidate(self, candidate_id: int) -> m.Candidate | None:
        with session() as s:
            return s.get(m.Candidate, candidate_id)

    def search_candidates(
        self,
        *,
        skills: list[str] | None = None,
        clearance: str | None = None,
        min_years: int = 0,
        location: str | None = None,
        query: str | None = None,
        limit: int = 20,
    ) -> list[m.Candidate]:
        with session() as s:
            cands = list(s.exec(select(m.Candidate)).all())

        results: list[tuple[float, m.Candidate]] = []
        for c in cands:
            if c.status == "do_not_contact":
                continue
            if query:
                blob = f"{c.name} {c.current_title} {' '.join(c.skills or [])} {c.resume_text}".lower()
                if query.lower() not in blob:
                    continue
            if location and location.lower() not in (c.location or "").lower():
                # keep remote candidates regardless of the requested location
                if not (c.location or "").lower().startswith("remote"):
                    continue
            score, _ = score_candidate(c, skills=skills, min_years=min_years, clearance=clearance)
            results.append((score, c))

        results.sort(key=lambda t: t[0], reverse=True)
        return [c for _, c in results[:limit]]

    def create_submission(
        self, *, candidate_id: int, job_id: int, stage: str = "matched",
        rank_score: float = 0.0, rationale: str = "",
    ) -> m.Submission:
        with session() as s:
            sub = m.Submission(
                candidate_id=candidate_id, job_id=job_id, stage=stage,
                rank_score=rank_score, rationale=rationale,
            )
            s.add(sub)
            s.commit()
            s.refresh(sub)
            return sub

    def update_submission(self, submission_id: int, **fields: Any) -> m.Submission | None:
        with session() as s:
            sub = s.get(m.Submission, submission_id)
            if not sub:
                return None
            for k, v in fields.items():
                setattr(sub, k, v)
            s.add(sub)
            s.commit()
            s.refresh(sub)
            return sub

    def save_rtr(
        self, *, candidate_id: int, authorized: bool, job_id: int | None = None,
        call_id: int | None = None, client_name: str = "", job_title: str = "",
        pay_rate: str = "", location: str = "", notes: str = "",
    ) -> m.RTR:
        with session() as s:
            rtr = m.RTR(
                candidate_id=candidate_id, authorized=authorized, job_id=job_id,
                call_id=call_id, client_name=client_name, job_title=job_title,
                pay_rate=pay_rate, location=location, notes=notes,
            )
            s.add(rtr)
            s.commit()
            s.refresh(rtr)
            return rtr
