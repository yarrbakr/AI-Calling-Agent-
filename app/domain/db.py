"""SQLite engine + session helpers.

SQLite is the $0, file-based store that the Mock CRM/ATS adapters read and write,
so the demo behaves like a real system of record without any cloud account.
"""

from __future__ import annotations

from collections.abc import Iterator

from sqlmodel import Session, SQLModel, create_engine

from app.config import DATA_DIR, settings

DATA_DIR.mkdir(parents=True, exist_ok=True)

# check_same_thread=False so FastAPI's threadpool can share the engine.
engine = create_engine(
    settings.db_url,
    echo=False,
    connect_args={"check_same_thread": False},
)


def init_db() -> None:
    """Create all tables. Importing models registers them on SQLModel.metadata."""
    from app.domain import models  # noqa: F401  (side effect: table registration)

    SQLModel.metadata.create_all(engine)


# expire_on_commit=False so records returned by the Mock adapters stay readable
# after their session closes (our models are flat — no lazy relationships).
def get_session() -> Iterator[Session]:
    """FastAPI dependency: yields a session and closes it afterwards."""
    with Session(engine, expire_on_commit=False) as session:
        yield session


def session() -> Session:
    """Standalone session for scripts/agents (use as a context manager)."""
    return Session(engine, expire_on_commit=False)
