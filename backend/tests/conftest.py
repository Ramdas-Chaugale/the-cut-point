"""Shared test fixtures: an in-memory SQLite session seeded for booking tests.

Using SQLite keeps the test suite self-contained (no Postgres needed in CI).
The booking service is database-agnostic, so the conflict logic is exercised
exactly as in production.
"""

from __future__ import annotations

from datetime import date, time
from typing import NamedTuple

import pytest
from app.models.tables import Service, Stylist, StylistAvailability, User
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

# A fixed Monday used across the booking tests.
MONDAY = date(2024, 1, 1)


class Seed(NamedTuple):
    user_id: int
    service_id: int  # 30-minute service
    stylist_id: int  # available Monday 09:00–12:00


@pytest.fixture
def session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


@pytest.fixture
def seed(session: Session) -> Seed:
    user = User(email="t@example.com", hashed_password="x", full_name="Test User")
    service = Service(name="Classic Cut", description="d", duration_minutes=30, price_pennies=2000)
    stylist = Stylist(name="Alex", bio="b")
    session.add_all([user, service, stylist])
    session.commit()
    session.refresh(user)
    session.refresh(service)
    session.refresh(stylist)
    session.add(
        StylistAvailability(
            stylist_id=stylist.id,
            day_of_week=0,  # Monday
            start_time=time(9, 0),
            end_time=time(12, 0),
        )
    )
    session.commit()
    assert user.id and service.id and stylist.id
    return Seed(user_id=user.id, service_id=service.id, stylist_id=stylist.id)
