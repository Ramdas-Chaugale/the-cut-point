"""Tests for the booking read endpoints (services / stylists / availability)."""

from __future__ import annotations

from datetime import date, timedelta

from app.core.db import get_session
from app.main import app
from fastapi.testclient import TestClient
from sqlmodel import Session

from .conftest import Seed


def _client(session: Session) -> TestClient:
    app.dependency_overrides[get_session] = lambda: session
    return TestClient(app)


def _next_monday() -> date:
    today = date.today()
    return today + timedelta(days=((7 - today.weekday()) % 7) or 7)


def test_services_endpoint(session: Session, seed: Seed) -> None:
    try:
        resp = _client(session).get("/api/services")
        assert resp.status_code == 200
        assert any(s["name"] == "Classic Cut" for s in resp.json())
    finally:
        app.dependency_overrides.clear()


def test_stylists_endpoint(session: Session, seed: Seed) -> None:
    try:
        resp = _client(session).get("/api/stylists")
        assert resp.status_code == 200
        assert any(s["name"] == "Alex" for s in resp.json())
    finally:
        app.dependency_overrides.clear()


def test_availability_endpoint_returns_future_slots(session: Session, seed: Seed) -> None:
    try:
        resp = _client(session).get(
            "/api/availability",
            params={
                "stylist_id": seed.stylist_id,
                "service_id": seed.service_id,
                "date": _next_monday().isoformat(),
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["slots"]) == 6  # 09:00–12:00, 30-min service
    finally:
        app.dependency_overrides.clear()


def test_availability_unknown_service_404(session: Session, seed: Seed) -> None:
    try:
        resp = _client(session).get(
            "/api/availability",
            params={
                "stylist_id": seed.stylist_id,
                "service_id": 99999,
                "date": _next_monday().isoformat(),
            },
        )
        assert resp.status_code == 404
    finally:
        app.dependency_overrides.clear()
