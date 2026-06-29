"""Shared test fixtures: an in-memory SQLite session seeded for booking tests.

SQLite keeps the suite self-contained (no Postgres in CI); the booking service
is database-agnostic, so the request/accept/decline logic runs as in production.
"""

from __future__ import annotations

from datetime import date, time
from typing import NamedTuple

import pytest
from app.core.security import hash_password
from app.models.tables import Salon, SalonAvailability, Service, User
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

# A fixed Monday used across booking tests.
MONDAY = date(2024, 1, 1)


class Seed(NamedTuple):
    client_id: int
    owner_id: int
    salon_id: int  # 1 chair, open Monday 09:00–12:00
    service_id: int  # 30-minute service


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
    client = User(
        email="client@test.com",
        hashed_password=hash_password("password123"),
        full_name="Test Client",
        role="client",
    )
    owner = User(
        email="owner@test.com",
        hashed_password=hash_password("password123"),
        full_name="Test Owner",
        role="saloon",
    )
    session.add_all([client, owner])
    session.commit()
    session.refresh(client)
    session.refresh(owner)

    salon = Salon(
        owner_id=owner.id,
        name="Test Salon",
        description="d",
        address="1 Test St",
        city="London",
        latitude=51.5,
        longitude=-0.1,
        phone="020 7000 0000",
        chairs=1,
    )
    session.add(salon)
    session.commit()
    session.refresh(salon)

    service = Service(
        salon_id=salon.id,
        name="Classic Cut",
        description="d",
        duration_minutes=30,
        price_pennies=2000,
    )
    session.add(service)
    session.commit()
    session.refresh(service)

    session.add(
        SalonAvailability(
            salon_id=salon.id, day_of_week=0, start_time=time(9, 0), end_time=time(12, 0)
        )
    )
    session.commit()

    assert client.id and owner.id and salon.id and service.id
    return Seed(client_id=client.id, owner_id=owner.id, salon_id=salon.id, service_id=service.id)
