"""Booking conflict + lifecycle tests — the core 'no double-booking' guarantee."""

from __future__ import annotations

from datetime import datetime

import pytest
from app.services import booking as svc
from sqlmodel import Session

from .conftest import MONDAY, Seed


def _at(hour: int, minute: int = 0) -> datetime:
    return datetime.combine(MONDAY, datetime.min.time()).replace(hour=hour, minute=minute)


def test_create_booking_succeeds(session: Session, seed: Seed) -> None:
    b = svc.create_booking(
        session,
        user_id=seed.user_id,
        stylist_id=seed.stylist_id,
        service_id=seed.service_id,
        start_at=_at(10),
    )
    assert b.id is not None
    assert b.end_at == _at(10, 30)
    assert b.status == "confirmed"


def test_overlapping_booking_is_rejected(session: Session, seed: Seed) -> None:
    svc.create_booking(
        session,
        user_id=seed.user_id,
        stylist_id=seed.stylist_id,
        service_id=seed.service_id,
        start_at=_at(10),
    )
    # 10:15 overlaps the 10:00–10:30 booking.
    with pytest.raises(svc.BookingError):
        svc.create_booking(
            session,
            user_id=seed.user_id,
            stylist_id=seed.stylist_id,
            service_id=seed.service_id,
            start_at=_at(10, 15),
        )


def test_back_to_back_bookings_allowed(session: Session, seed: Seed) -> None:
    svc.create_booking(
        session,
        user_id=seed.user_id,
        stylist_id=seed.stylist_id,
        service_id=seed.service_id,
        start_at=_at(10),
    )
    # 10:30 starts exactly when the previous ends — no overlap.
    b = svc.create_booking(
        session,
        user_id=seed.user_id,
        stylist_id=seed.stylist_id,
        service_id=seed.service_id,
        start_at=_at(10, 30),
    )
    assert b.id is not None


def test_booking_outside_working_hours_rejected(session: Session, seed: Seed) -> None:
    # 08:00 is before the 09:00 window start.
    with pytest.raises(svc.BookingError):
        svc.create_booking(
            session,
            user_id=seed.user_id,
            stylist_id=seed.stylist_id,
            service_id=seed.service_id,
            start_at=_at(8),
        )
    # 11:45 + 30min would end at 12:15, past the 12:00 window end.
    with pytest.raises(svc.BookingError):
        svc.create_booking(
            session,
            user_id=seed.user_id,
            stylist_id=seed.stylist_id,
            service_id=seed.service_id,
            start_at=_at(11, 45),
        )


def test_cancel_frees_the_slot(session: Session, seed: Seed) -> None:
    b = svc.create_booking(
        session,
        user_id=seed.user_id,
        stylist_id=seed.stylist_id,
        service_id=seed.service_id,
        start_at=_at(10),
    )
    # Slot is taken now.
    assert svc.has_conflict(session, seed.stylist_id, _at(10), _at(10, 30))
    svc.cancel_booking(session, b.id, seed.user_id)
    # Slot is free again after cancellation.
    assert not svc.has_conflict(session, seed.stylist_id, _at(10), _at(10, 30))


def test_cancel_requires_ownership(session: Session, seed: Seed) -> None:
    b = svc.create_booking(
        session,
        user_id=seed.user_id,
        stylist_id=seed.stylist_id,
        service_id=seed.service_id,
        start_at=_at(10),
    )
    with pytest.raises(svc.BookingError):
        svc.cancel_booking(session, b.id, user_id=seed.user_id + 999)


def test_list_user_bookings(session: Session, seed: Seed) -> None:
    svc.create_booking(
        session,
        user_id=seed.user_id,
        stylist_id=seed.stylist_id,
        service_id=seed.service_id,
        start_at=_at(10),
    )
    bookings = svc.list_user_bookings(session, seed.user_id)
    assert len(bookings) == 1
    assert svc.list_user_bookings(session, seed.user_id + 999) == []
