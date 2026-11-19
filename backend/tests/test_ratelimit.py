"""Rate limiting on the try-on route.

That endpoint spends money or free-tier quota at an image provider on every
call, and it is public with no auth, so the limit is the only thing between a
loop and an empty credit balance. These tests never reach a provider: the
generator is replaced and the settings are fake.
"""

from __future__ import annotations

import pytest
from app.api import tryon as route
from app.core.db import get_session
from app.main import app
from app.services import ratelimit
from app.services import tryon as svc
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

_IMG = "data:image/jpeg;base64," + "A" * 64


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
def client(session: Session, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """A client whose try-on never calls a provider and whose db is in memory."""
    monkeypatch.setattr(svc, "generate_tryon", lambda *a, **k: "https://example.test/x.png")
    app.dependency_overrides[get_session] = lambda: session
    yield TestClient(app)
    app.dependency_overrides.clear()


def _post(c: TestClient, ip: str):
    return c.post(
        "/api/tryon/generate",
        json={"image_data_url": _IMG, "style_id": "burst-fade"},
        headers={"x-forwarded-for": ip},
    )


# --- the counter itself ------------------------------------------------------


def test_counts_down_then_blocks(session: Session) -> None:
    for expected_remaining in (2, 1, 0):
        d = ratelimit.check(session, bucket="b", key="1.2.3.4", limit=3, window_seconds=60)
        assert d.allowed
        assert d.remaining == expected_remaining

    blocked = ratelimit.check(session, bucket="b", key="1.2.3.4", limit=3, window_seconds=60)
    assert not blocked.allowed
    assert blocked.remaining == 0
    assert blocked.retry_after > 0


def test_callers_are_counted_separately(session: Session) -> None:
    for _ in range(3):
        ratelimit.check(session, bucket="b", key="1.1.1.1", limit=3, window_seconds=60)

    other = ratelimit.check(session, bucket="b", key="2.2.2.2", limit=3, window_seconds=60)
    assert other.allowed, "one caller's usage must not limit another"


def test_buckets_are_counted_separately(session: Session) -> None:
    for _ in range(3):
        ratelimit.check(session, bucket="tryon", key="1.1.1.1", limit=3, window_seconds=60)

    other = ratelimit.check(session, bucket="assistant", key="1.1.1.1", limit=3, window_seconds=60)
    assert other.allowed, "limiting one endpoint must not limit a different one"


def test_sweep_drops_old_windows(session: Session) -> None:
    ratelimit.check(session, bucket="b", key="1.1.1.1", limit=3, window_seconds=60)
    assert ratelimit.sweep(session, older_than_seconds=0) >= 1


# --- the route ---------------------------------------------------------------


def test_route_allows_up_to_the_limit(client: TestClient) -> None:
    for _ in range(route.TRYON_LIMIT):
        assert _post(client, "198.51.100.1").status_code == 200


def test_route_blocks_past_the_limit(client: TestClient) -> None:
    for _ in range(route.TRYON_LIMIT):
        _post(client, "198.51.100.2")

    over = _post(client, "198.51.100.2")
    assert over.status_code == 429
    assert "Retry-After" in over.headers
    assert over.headers["X-RateLimit-Remaining"] == "0"


def test_route_limit_is_per_caller(client: TestClient) -> None:
    for _ in range(route.TRYON_LIMIT):
        _post(client, "198.51.100.3")

    assert (
        _post(client, "198.51.100.4").status_code == 200
    ), "exhausting one IP must not lock out everyone else"


def test_remaining_header_counts_down(client: TestClient) -> None:
    first = _post(client, "198.51.100.5")
    assert int(first.headers["X-RateLimit-Remaining"]) == route.TRYON_LIMIT - 1


def test_limit_endpoint_reports_the_policy(client: TestClient) -> None:
    body = client.get("/api/tryon/limit").json()
    assert body["limit"] == route.TRYON_LIMIT
    assert body["window_seconds"] == route.TRYON_WINDOW_SECONDS
