"""Slot generation: windows, duration fit, capacity (confirmed bookings)."""

from __future__ import annotations

from datetime import datetime

from app.services import booking as svc
from sqlmodel import Session

from .conftest import MONDAY, Seed


def _at(hour: int, minute: int = 0) -> datetime:
    return datetime.combine(MONDAY, datetime.min.time()).replace(hour=hour, minute=minute)


def test_slots_span_the_window(session: Session, seed: Seed) -> None:
    # 09:00–12:00, 30-min service, 30-min step -> 6 start times.
    slots = svc.available_slots(session, seed.salon_id, seed.service_id, MONDAY)
    assert slots == [_at(9), _at(9, 30), _at(10), _at(10, 30), _at(11), _at(11, 30)]


def test_no_slots_on_a_day_off(session: Session, seed: Seed) -> None:
    tuesday = MONDAY.replace(day=MONDAY.day + 1)
    assert svc.available_slots(session, seed.salon_id, seed.service_id, tuesday) == []


def test_confirmed_booking_removes_slot(session: Session, seed: Seed) -> None:
    b = svc.request_booking(
        session,
        client_id=seed.client_id,
        salon_id=seed.salon_id,
        service_id=seed.service_id,
        start_at=_at(10),
    )
    # Still available while only pending...
    assert _at(10) in svc.available_slots(session, seed.salon_id, seed.service_id, MONDAY)
    # ...removed once confirmed (1 chair).
    svc.accept_booking(session, seed.owner_id, b.id)
    slots = svc.available_slots(session, seed.salon_id, seed.service_id, MONDAY)
    assert _at(10) not in slots
    assert _at(9, 30) in slots
    assert _at(10, 30) in slots


def test_now_filter_drops_past_slots(session: Session, seed: Seed) -> None:
    slots = svc.available_slots(session, seed.salon_id, seed.service_id, MONDAY, now=_at(10))
    assert all(s > _at(10) for s in slots)
