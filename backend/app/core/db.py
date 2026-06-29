"""Database engine and session management."""

from __future__ import annotations

from collections.abc import Iterator

from sqlmodel import Session, create_engine

from app.core.config import get_settings

settings = get_settings()

# pool_pre_ping avoids stale connections after the DB sleeps (free-tier hosts).
engine = create_engine(settings.database_url, echo=False, pool_pre_ping=True)


def get_session() -> Iterator[Session]:
    """FastAPI dependency yielding a database session."""
    with Session(engine) as session:
        yield session
