"""Booking API tests over HTTP: discovery, availability, request/accept flow."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

import pytest
from app.core.db import get_session
from app.core.security import create_access_token
from app.main import app
from fastapi.testclient import TestClient
from sqlmodel import Session

from .conftest import MONDAY, Seed


def _client(session: Session) -> TestClient:
    app.dependency_overrides[get_session] = lambda: session
    return TestClient(app)


def _auth(user_id: int, role: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user_id, role)}"}


def _next_monday() -> date:
    today = date.today()
    return today + timedelta(days=((7 - today.weekday()) % 7) or 7)


@pytest.fixture(autouse=True)
def _clear() -> None:
    yield
    app.dependency_overrides.clear()


def test_list_and_detail(session: Session, seed: Seed) -> None:
    c = _client(session)
    salons = c.get("/api/salons").json()
    assert any(s["id"] == seed.salon_id for s in salons)
    detail = c.get(f"/api/salons/{seed.salon_id}").json()
    assert any(s["id"] == seed.service_id for s in detail["services"])


def test_availability_endpoint(session: Session, seed: Seed) -> None:
    c = _client(session)
    resp = c.get(
        f"/api/salons/{seed.salon_id}/availability",
        params={"service_id": seed.service_id, "date": _next_monday().isoformat()},
    )
    assert resp.status_code == 200
    assert len(resp.json()["slots"]) == 6  # 09:00–12:00, 30-min service


def test_request_then_accept_flow(session: Session, seed: Seed) -> None:
    c = _client(session)
    start = datetime.combine(MONDAY, time(10, 0)).isoformat()

    req = c.post(
        "/api/bookings",
        json={"salon_id": seed.salon_id, "service_id": seed.service_id, "start_at": start},
        headers=_auth(seed.client_id, "client"),
    )
    assert req.status_code == 200
    booking = req.json()
    assert booking["status"] == "pending"
    assert booking["service_name"] == "Classic Cut"

    # Owner sees the request and accepts it.
    listing = c.get("/api/salon/bookings", headers=_auth(seed.owner_id, "saloon"))
    assert any(b["id"] == booking["id"] for b in listing.json())

    accept = c.post(f"/api/bookings/{booking['id']}/accept", headers=_auth(seed.owner_id, "saloon"))
    assert accept.status_code == 200
    assert accept.json()["status"] == "confirmed"


def test_client_cannot_accept(session: Session, seed: Seed) -> None:
    c = _client(session)
    start = datetime.combine(MONDAY, time(10, 0)).isoformat()
    req = c.post(
        "/api/bookings",
        json={"salon_id": seed.salon_id, "service_id": seed.service_id, "start_at": start},
        headers=_auth(seed.client_id, "client"),
    )
    bid = req.json()["id"]
    forbidden = c.post(f"/api/bookings/{bid}/accept", headers=_auth(seed.client_id, "client"))
    assert forbidden.status_code == 403


def test_request_requires_client_role(session: Session, seed: Seed) -> None:
    c = _client(session)
    start = datetime.combine(MONDAY, time(10, 0)).isoformat()
    resp = c.post(
        "/api/bookings",
        json={"salon_id": seed.salon_id, "service_id": seed.service_id, "start_at": start},
        headers=_auth(seed.owner_id, "saloon"),
    )
    assert resp.status_code == 403


def test_stats_endpoint(session: Session, seed: Seed) -> None:
    c = _client(session)
    resp = c.get("/api/salon/stats", headers=_auth(seed.owner_id, "saloon"))
    assert resp.status_code == 200
    assert set(resp.json()) >= {"pending_requests", "revenue_pennies", "unique_clients"}
