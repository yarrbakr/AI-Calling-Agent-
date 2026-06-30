"""CRM port — the Zoho-shaped interface the Sales/AM agents depend on.

Methods map onto Zoho CRM modules: Leads, Contacts, Accounts, Calls (call logging),
Events (meetings), Tasks. The Mock adapter persists to SQLite; the real ZohoAdapter
maps the same calls onto /crm/v2 (see research/20260630-230002...).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from app.domain import models as m


class CrmPort(ABC):
    name: str = "crm"

    # --- Leads (Zoho Leads) ---
    @abstractmethod
    def list_leads(self, status: str | None = None) -> list[m.Lead]: ...

    @abstractmethod
    def get_lead(self, lead_id: int) -> m.Lead | None: ...

    @abstractmethod
    def create_lead(self, **fields: Any) -> m.Lead: ...

    @abstractmethod
    def update_lead(self, lead_id: int, **fields: Any) -> m.Lead | None: ...

    # --- Accounts / Contacts ---
    @abstractmethod
    def list_clients(self) -> list[m.Client]: ...

    @abstractmethod
    def get_client(self, client_id: int) -> m.Client | None: ...

    @abstractmethod
    def create_contact(self, **fields: Any) -> m.Contact: ...

    # --- Activity: Calls, Events (meetings), Tasks ---
    @abstractmethod
    def log_call(self, **fields: Any) -> m.Call: ...

    @abstractmethod
    def schedule_meeting(self, *, scheduled_for: datetime, **fields: Any) -> m.Meeting: ...

    @abstractmethod
    def create_task(self, **fields: Any) -> m.Task: ...
