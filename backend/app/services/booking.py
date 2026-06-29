"""Availability and booking logic — the conflict-free core of the salon side.

The key guarantee: a stylist can never hold two overlapping confirmed bookings.
All functions take an explicit Session so they're easy to unit-test against any
database (the tests use SQLite in-memory).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlmodel import Session, select

from app.models.tables import Booking, Service, Stylist, StylistAvailability

# Bookable start times are offered on this granularity within working windows.
SLOT_STEP_MINUTES = 30


class BookingError(Exception):
    """Raised when a booking cannot be made (conflict, outside hours, etc.)."""


def list_services(session: Session) -> list[Service]:
    return list(session.exec(select(Service).where(Service.active).order_by(Service.name)))


def list_stylists(session: Session) -> list[Stylist]:
    return list(session.exec(select(Stylist).where(Stylist.active).order_by(Stylist.name)))


def get_service(session: Session, service_id: int) -> Service:
    service = session.get(Service, service_id)
    if service is None or not service.active:
        raise BookingError("That service is not available.")
    return service


def get_stylist(session: Session, stylist_id: int) -> Stylist:
    stylist = session.get(Stylist, stylist_id)
    if stylist is None or not stylist.active:
        raise BookingError("That stylist is not available.")
    return stylist


def has_conflict(
    session: Session,
    stylist_id: int,
    start_at: datetime,
    end_at: datetime,
    *,
    exclude_booking_id: int | None = None,
) -> bool:
    """True if a confirmed booking for this stylist overlaps [start_at, end_at).

    Overlap test: existing.start < new.end AND existing.end > new.start.
    """
    stmt = select(Booking).where(
        Booking.stylist_id == stylist_id,
        Booking.status == "confirmed",
        Booking.start_at < end_at,
        Booking.end_at > start_at,
    )
    if exclude_booking_id is not None:
        stmt = stmt.where(Booking.id != exclude_booking_id)
    return session.exec(stmt).first() is not None


def _windows_for(session: Session, stylist_id: int, weekday: int) -> list[StylistAvailability]:
    return list(
        session.exec(
            select(StylistAvailability).where(
                StylistAvailability.stylist_id == stylist_id,
                StylistAvailability.day_of_week == weekday,
            )
        )
    )


def available_slots(
    session: Session,
    stylist_id: int,
    service_id: int,
    on_date: date,
    *,
    now: datetime | None = None,
) -> list[datetime]:
    """Return bookable start times for a stylist+service on a given date.

    A slot is offered only if the full service duration fits inside a working
    window and does not overlap an existing confirmed booking. If ``now`` is
    given, slots starting at or before it are dropped (no booking in the past).
    """
    service = get_service(session, service_id)
    get_stylist(session, stylist_id)
    duration = timedelta(minutes=service.duration_minutes)
    step = timedelta(minutes=SLOT_STEP_MINUTES)

    slots: list[datetime] = []
    for window in _windows_for(session, stylist_id, on_date.weekday()):
        window_start = datetime.combine(on_date, window.start_time)
        window_end = datetime.combine(on_date, window.end_time)
        start = window_start
        while start + duration <= window_end:
            end = start + duration
            future = now is None or start > now
            if future and not has_conflict(session, stylist_id, start, end):
                slots.append(start)
            start += step
    return slots


def create_booking(
    session: Session,
    *,
    user_id: int,
    stylist_id: int,
    service_id: int,
    start_at: datetime,
    look_style_id: str | None = None,
) -> Booking:
    """Create a confirmed booking, rejecting conflicts and out-of-hours times."""
    service = get_service(session, service_id)
    get_stylist(session, stylist_id)
    end_at = start_at + timedelta(minutes=service.duration_minutes)

    # Must fall entirely within one of the stylist's working windows that day.
    in_hours = any(
        w.start_time <= start_at.time() and end_at.time() <= w.end_time
        for w in _windows_for(session, stylist_id, start_at.weekday())
    )
    if not in_hours:
        raise BookingError("That time is outside the stylist's working hours.")

    if has_conflict(session, stylist_id, start_at, end_at):
        raise BookingError("That slot has just been taken. Please pick another time.")

    booking = Booking(
        user_id=user_id,
        stylist_id=stylist_id,
        service_id=service_id,
        start_at=start_at,
        end_at=end_at,
        look_style_id=look_style_id,
    )
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return booking


def cancel_booking(session: Session, booking_id: int, user_id: int) -> Booking:
    """Soft-cancel a booking owned by the user (keeps history, frees the slot)."""
    booking = session.get(Booking, booking_id)
    if booking is None or booking.user_id != user_id:
        raise BookingError("Booking not found.")
    booking.status = "cancelled"
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return booking


def list_user_bookings(session: Session, user_id: int) -> list[Booking]:
    return list(
        session.exec(
            select(Booking)
            .where(Booking.user_id == user_id)
            .order_by(Booking.start_at.desc())  # type: ignore[attr-defined]
        )
    )
