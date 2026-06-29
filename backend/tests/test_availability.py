"""Slot-generation tests: windows, duration fit, and booked-slot removal."""

from __future__ import annotations

from datetime import datetime

from app.services import booking as svc
from sqlmodel import Session

from .conftest import MONDAY, Seed


def _at(hour: int, minute: int = 0) -> datetime:
    return datetime.combine(MONDAY, datetime.min.time()).replace(hour=hour, minute=minute)


def test_slots_span_the_window(session: Session, seed: Seed) -> None:
    # 09:00–12:00 window, 30-min service, 30-min step -> 6 start times.
    slots = svc.available_slots(session, seed.stylist_id, seed.service_id, MONDAY)
    assert slots == [_at(9), _at(9, 30), _at(10), _at(10, 30), _at(11), _at(11, 30)]


def test_no_slots_on_a_day_off(session: Session, seed: Seed) -> None:
    # The stylist only works Mondays; Tuesday has no windows.
    tuesday = MONDAY.replace(day=MONDAY.day + 1)
    assert svc.available_slots(session, seed.stylist_id, seed.service_id, tuesday) == []


def test_booked_slot_is_removed(session: Session, seed: Seed) -> None:
    svc.create_booking(
        session,
        user_id=seed.user_id,
        stylist_id=seed.stylist_id,
        service_id=seed.service_id,
        start_at=_at(10),
    )
    slots = svc.available_slots(session, seed.stylist_id, seed.service_id, MONDAY)
    assert _at(10) not in slots
    assert _at(9, 30) in slots  # adjacent, no overlap
    assert _at(10, 30) in slots
    assert len(slots) == 5


def test_now_filter_drops_past_slots(session: Session, seed: Seed) -> None:
    # Pretend "now" is 10:00 — only 10:30 and 11:00, 11:30 remain.
    slots = svc.available_slots(session, seed.stylist_id, seed.service_id, MONDAY, now=_at(10))
    assert all(s > _at(10) for s in slots)
    assert _at(10, 30) in slots
