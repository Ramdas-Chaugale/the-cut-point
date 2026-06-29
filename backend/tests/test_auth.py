"""Auth endpoint tests: register (client/saloon), login, me."""

from __future__ import annotations

import pytest
from app.core.db import get_session
from app.main import app
from fastapi.testclient import TestClient
from sqlmodel import Session

_CLIENT_BODY = {"email": "a@b.com", "password": "password123", "full_name": "Ada"}
_SALOON_BODY = {
    "email": "shop@b.com",
    "password": "password123",
    "full_name": "Owner",
    "salon": {
        "name": "Test Shop",
        "address": "1 Test St",
        "city": "London",
        "latitude": 51.5,
        "longitude": -0.1,
        "phone": "020 7000 0000",
    },
}


def _client(session: Session) -> TestClient:
    app.dependency_overrides[get_session] = lambda: session
    return TestClient(app)


@pytest.fixture(autouse=True)
def _clear() -> None:
    yield
    app.dependency_overrides.clear()


def test_register_login_me_client(session: Session) -> None:
    c = _client(session)
    reg = c.post("/api/auth/register/client", json=_CLIENT_BODY)
    assert reg.status_code == 200
    token = reg.json()["access_token"]
    assert reg.json()["user"]["role"] == "client"

    login = c.post("/api/auth/login", json={"email": "a@b.com", "password": "password123"})
    assert login.status_code == 200

    me = c.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["user"]["email"] == "a@b.com"
    assert me.json()["salon_id"] is None


def test_register_saloon_creates_salon(session: Session) -> None:
    c = _client(session)
    reg = c.post("/api/auth/register/saloon", json=_SALOON_BODY)
    assert reg.status_code == 200
    assert reg.json()["salon_id"] is not None
    salons = c.get("/api/salons").json()
    assert any(s["name"] == "Test Shop" for s in salons)


def test_duplicate_email_rejected(session: Session) -> None:
    c = _client(session)
    c.post("/api/auth/register/client", json=_CLIENT_BODY)
    again = c.post("/api/auth/register/client", json=_CLIENT_BODY)
    assert again.status_code == 400


def test_wrong_password_401(session: Session) -> None:
    c = _client(session)
    c.post("/api/auth/register/client", json=_CLIENT_BODY)
    bad = c.post("/api/auth/login", json={"email": "a@b.com", "password": "wrong"})
    assert bad.status_code == 401


def test_me_requires_auth(session: Session) -> None:
    assert _client(session).get("/api/auth/me").status_code == 401


def test_short_password_rejected(session: Session) -> None:
    c = _client(session)
    bad = c.post(
        "/api/auth/register/client",
        json={"email": "x@y.com", "password": "short", "full_name": "X"},
    )
    assert bad.status_code == 422
