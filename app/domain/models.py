"""Domain entities (SQLModel tables).

These model the slice of a recruitment/staffing system the brief touches:
CRM-side (Clients, Leads, Contacts, Meetings) and ATS-side (Jobs, Candidates,
Submissions, RTRs), plus cross-cutting activity (Calls, TranscriptTurns,
Messages, Tasks, SurveyResponses).

List/dict fields are stored as JSON columns to keep the schema simple while
still holding structured data (skills, payloads, etc.).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlmodel import JSON, Column, Field, SQLModel


def _now() -> datetime:
    # Naive UTC, avoiding the deprecated datetime.utcnow().
    return datetime.now(timezone.utc).replace(tzinfo=None)


# --------------------------------------------------------------------------- #
# CRM side (Zoho): clients, leads, contacts, meetings
# --------------------------------------------------------------------------- #
class Client(SQLModel, table=True):
    """A client account (Zoho 'Account'). Owned by an Account Manager."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    industry: str = "Federal / Government Services"
    account_manager: str = ""
    health: str = "good"          # good | at_risk | churned
    csat_avg: float = 0.0
    notes: str = ""
    created_at: datetime = Field(default_factory=_now)


class Lead(SQLModel, table=True):
    """A sales lead (Zoho 'Lead') for the qualification agent to work."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    company: str = ""
    title: str = ""
    phone: str = ""
    email: str = ""
    source: str = "inbound"       # inbound | list | referral | event
    status: str = "new"           # new | qualifying | qualified | disqualified | nurturing
    score: int = 0                # 0-100 qualification score
    budget: str = ""
    authority: str = ""
    need: str = ""
    timeline: str = ""
    notes: str = ""
    created_at: datetime = Field(default_factory=_now)


class Contact(SQLModel, table=True):
    """A person at a client account (Zoho 'Contact')."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    title: str = ""
    phone: str = ""
    email: str = ""
    client_id: Optional[int] = Field(default=None, foreign_key="client.id")
    created_at: datetime = Field(default_factory=_now)


class Meeting(SQLModel, table=True):
    """A scheduled meeting/demo booked by the sales agent."""

    id: Optional[int] = Field(default=None, primary_key=True)
    subject: str = "Intro meeting"
    scheduled_for: datetime
    lead_id: Optional[int] = Field(default=None, foreign_key="lead.id")
    contact_id: Optional[int] = Field(default=None, foreign_key="contact.id")
    location: str = "Google Meet"
    notes: str = ""
    created_at: datetime = Field(default_factory=_now)


# --------------------------------------------------------------------------- #
# ATS side (Ceipal): jobs, candidates, submissions
# --------------------------------------------------------------------------- #
class Job(SQLModel, table=True):
    """A job requisition (Ceipal 'Requirement')."""

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    client_id: Optional[int] = Field(default=None, foreign_key="client.id")
    client_name: str = ""
    location: str = ""
    remote: bool = False
    clearance: str = "None"       # None | Public Trust | Secret | Top Secret | TS/SCI
    employment_type: str = "W2"   # W2 | C2C | 1099
    min_years: int = 0
    pay_rate: str = ""
    skills: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    description: str = ""
    status: str = "open"          # open | filled | on_hold
    created_at: datetime = Field(default_factory=_now)


class Candidate(SQLModel, table=True):
    """A candidate in the ATS database (Ceipal)."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    phone: str = ""
    email: str = ""
    location: str = ""
    clearance: str = "None"
    work_authorization: str = "US Citizen"  # US Citizen | GC | H1B | OPT | ...
    years_experience: int = 0
    current_title: str = ""
    desired_rate: str = ""
    skills: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    resume_text: str = ""
    status: str = "active"        # active | submitted | placed | do_not_contact
    source: str = "internal"      # internal | job_board | referral
    created_at: datetime = Field(default_factory=_now)


class Submission(SQLModel, table=True):
    """A candidate submitted/matched to a job, with a relevancy/rank score."""

    id: Optional[int] = Field(default=None, primary_key=True)
    candidate_id: int = Field(foreign_key="candidate.id")
    job_id: int = Field(foreign_key="job.id")
    stage: str = "matched"        # matched | screening | submitted | interview | placed | rejected
    rank_score: float = 0.0       # 0-100 match score
    rationale: str = ""
    created_at: datetime = Field(default_factory=_now)


# --------------------------------------------------------------------------- #
# Activity: calls, transcripts, RTRs, messages, tasks, surveys
# --------------------------------------------------------------------------- #
class Call(SQLModel, table=True):
    """A voice interaction handled by an agent (real or simulated)."""

    id: Optional[int] = Field(default=None, primary_key=True)
    direction: str = "outbound"   # outbound | inbound
    agent_type: str = "voice_screening"
    party_type: str = "candidate"  # candidate | lead | contact | client
    party_id: Optional[int] = None
    job_id: Optional[int] = Field(default=None, foreign_key="job.id")
    status: str = "in_progress"   # in_progress | completed | failed | no_answer
    outcome: str = ""             # e.g. interested | not_interested | rtr_collected
    summary: str = ""
    structured: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    recording_path: str = ""
    started_at: datetime = Field(default_factory=_now)
    ended_at: Optional[datetime] = None


class TranscriptTurn(SQLModel, table=True):
    """One utterance within a call (agent or human)."""

    id: Optional[int] = Field(default=None, primary_key=True)
    call_id: int = Field(foreign_key="call.id")
    role: str                      # agent | human | system
    text: str
    ts: datetime = Field(default_factory=_now)


class RTR(SQLModel, table=True):
    """A captured Right To Represent authorization from a screening call."""

    id: Optional[int] = Field(default=None, primary_key=True)
    candidate_id: int = Field(foreign_key="candidate.id")
    job_id: Optional[int] = Field(default=None, foreign_key="job.id")
    call_id: Optional[int] = Field(default=None, foreign_key="call.id")
    client_name: str = ""
    job_title: str = ""
    pay_rate: str = ""
    location: str = ""
    authorized: bool = False
    notes: str = ""
    captured_at: datetime = Field(default_factory=_now)


class Message(SQLModel, table=True):
    """An outbound message on any channel (the multi-channel follow-up log)."""

    id: Optional[int] = Field(default=None, primary_key=True)
    channel: str                   # sms | whatsapp | email | voice
    to_addr: str = ""
    subject: str = ""
    body: str = ""
    status: str = "queued"         # queued | sent | failed
    about_type: str = ""           # lead | candidate | client | contact
    about_id: Optional[int] = None
    provider: str = "mock"
    created_at: datetime = Field(default_factory=_now)


class Task(SQLModel, table=True):
    """A unit of work for an agent or a human (follow-up, escalation, survey...)."""

    id: Optional[int] = Field(default=None, primary_key=True)
    type: str                      # followup | escalation | status_update | survey | nurture
    channel: str = "phone"         # phone | sms | whatsapp | email
    about_type: str = ""           # lead | candidate | client | contact
    about_id: Optional[int] = None
    assignee: str = "ai-agent"     # ai-agent | <human name>
    status: str = "open"           # open | done | cancelled
    due_at: Optional[datetime] = None
    payload: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    notes: str = ""
    created_at: datetime = Field(default_factory=_now)


class SurveyResponse(SQLModel, table=True):
    """A client satisfaction (CSAT) survey result captured by the AM agent."""

    id: Optional[int] = Field(default=None, primary_key=True)
    client_id: Optional[int] = Field(default=None, foreign_key="client.id")
    call_id: Optional[int] = Field(default=None, foreign_key="call.id")
    csat_score: int = 0            # 1-5
    sentiment: str = "neutral"     # positive | neutral | negative
    comments: str = ""
    escalated: bool = False
    captured_at: datetime = Field(default_factory=_now)
