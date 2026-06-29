"""Request/accept/decline flow + the no-double-booking (capacity) guarantee."""

from __future__ import annotations

from datetime import datetime

import pytest
from app.models.tables import CONFIRMED, DECLINED, PENDING
from app.services import booking as svc
from sqlmodel import Session

from .conftest import MONDAY, Seed


def _at(hour: int, minute: int = 0) -> datetime:
    return datetime.combine(MONDAY, datetime.min.time()).replace(hour=hour, minute=minute)


def _request(session: Session, seed: Seed, hour: int, minute: int = 0):
    return svc.request_booking(
        session,
        client_id=seed.client_id,
        salon_id=seed.salon_id,
        service_id=seed.service_id,
        start_at=_at(hour, minute),
    )


def test_request_creates_pending(session: Session, seed: Seed) -> None:
    b = _request(session, seed, 10)
    assert b.status == PENDING
    assert b.end_at == _at(10, 30)


def test_pending_requests_do_not_consume_capacity(session: Session, seed: Seed) -> None:
    # Two clients can both request the same slot; capacity is only used on accept.
    _request(session, seed, 10)
    b2 = _request(session, seed, 10)
    assert b2.status == PENDING


def test_accept_confirms_and_fills_capacity(session: Session, seed: Seed) -> None:
    b1 = _request(session, seed, 10)
    b2 = _request(session, seed, 10)
    accepted = svc.accept_booking(session, seed.owner_id, b1.id)
    assert accepted.status == CONFIRMED
    # Salon has 1 chair, so the overlapping second request can't be accepted.
    with pytest.raises(svc.BookingError):
        svc.accept_booking(session, seed.owner_id, b2.id)


def test_request_rejected_when_slot_full(session: Session, seed: Seed) -> None:
    b1 = _request(session, seed, 10)
    svc.accept_booking(session, seed.owner_id, b1.id)
    # Now a confirmed booking fills the only chair — new overlapping request fails.
    with pytest.raises(svc.BookingError):
        _request(session, seed, 10, 15)


def test_back_to_back_allowed(session: Session, seed: Seed) -> None:
    b1 = _request(session, seed, 10)
    svc.accept_booking(session, seed.owner_id, b1.id)
    b2 = _request(session, seed, 10, 30)  # starts as the first ends
    assert b2.status == PENDING


def test_out_of_hours_rejected(session: Session, seed: Seed) -> None:
    with pytest.raises(svc.BookingError):
        _request(session, seed, 8)  # before 09:00
    with pytest.raises(svc.BookingError):
        _request(session, seed, 11, 45)  # would end 12:15, past 12:00


def test_decline_with_suggestion(session: Session, seed: Seed) -> None:
    b = _request(session, seed, 10)
    declined = svc.decline_booking(session, seed.owner_id, b.id, suggested_start_at=_at(11))
    assert declined.status == DECLINED
    assert declined.suggested_start_at == _at(11)


def test_accept_requires_ownership(session: Session, seed: Seed) -> None:
    b = _request(session, seed, 10)
    with pytest.raises(svc.BookingError):
        svc.accept_booking(session, seed.owner_id + 999, b.id)


def test_cancel_frees_capacity(session: Session, seed: Seed) -> None:
    b = _request(session, seed, 10)
    svc.accept_booking(session, seed.owner_id, b.id)
    assert not svc.has_capacity(
        session, svc.get_salon(session, seed.salon_id), _at(10), _at(10, 30)
    )
    svc.cancel_booking(session, seed.client_id, b.id)
    assert svc.has_capacity(session, svc.get_salon(session, seed.salon_id), _at(10), _at(10, 30))


def test_stats(session: Session, seed: Seed) -> None:
    b = _request(session, seed, 10)
    svc.accept_booking(session, seed.owner_id, b.id)
    stats = svc.salon_stats(session, seed.salon_id, now=_at(9))
    assert stats["upcoming_confirmed"] == 1
    assert stats["revenue_pennies"] == 2000
    assert stats["unique_clients"] == 1
