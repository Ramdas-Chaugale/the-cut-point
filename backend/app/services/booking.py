"""Availability + booking logic for the request → accept/decline flow.

A client *requests* a slot (status ``pending``); the salon owner *accepts*
(``confirmed``) or *declines* (``declined``, optionally suggesting a new time).
A salon serves up to ``chairs`` clients at once, so the capacity rule is:
the number of *confirmed* bookings overlapping a time must stay below ``chairs``.
Pending requests don't consume capacity — several clients may request the same
slot, and the owner decides who gets it.

All functions take an explicit Session, so the logic is unit-tested against
SQLite in-memory (no Postgres needed in CI).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlmodel import Session, select

from app.models.tables import (
    CANCELLED,
    CONFIRMED,
    DECLINED,
    PENDING,
    Booking,
    Salon,
    SalonAvailability,
    Service,
)

SLOT_STEP_MINUTES = 30


class BookingError(Exception):
    """Raised when a booking action is invalid (conflict, out-of-hours, etc.)."""


# --- lookups -------------------------------------------------------------


def list_salons(session: Session, *, city: str | None = None) -> list[Salon]:
    stmt = select(Salon)
    if city:
        stmt = stmt.where(Salon.city == city)
    return list(session.exec(stmt.order_by(Salon.name)))


def get_salon(session: Session, salon_id: int) -> Salon:
    salon = session.get(Salon, salon_id)
    if salon is None:
        raise BookingError("Salon not found.")
    return salon


def list_services(session: Session, salon_id: int) -> list[Service]:
    return list(
        session.exec(
            select(Service)
            .where(Service.salon_id == salon_id, Service.active)
            .order_by(Service.name)
        )
    )


def get_service(session: Session, service_id: int, salon_id: int) -> Service:
    service = session.get(Service, service_id)
    if service is None or not service.active or service.salon_id != salon_id:
        raise BookingError("That service is not available at this salon.")
    return service


# --- capacity / availability --------------------------------------------


def confirmed_overlap_count(
    session: Session,
    salon_id: int,
    start_at: datetime,
    end_at: datetime,
    *,
    exclude_booking_id: int | None = None,
) -> int:
    """Count confirmed bookings for a salon overlapping [start_at, end_at)."""
    stmt = select(Booking).where(
        Booking.salon_id == salon_id,
        Booking.status == CONFIRMED,
        Booking.start_at < end_at,
        Booking.end_at > start_at,
    )
    if exclude_booking_id is not None:
        stmt = stmt.where(Booking.id != exclude_booking_id)
    return len(list(session.exec(stmt)))


def has_capacity(
    session: Session,
    salon: Salon,
    start_at: datetime,
    end_at: datetime,
    *,
    exclude_booking_id: int | None = None,
) -> bool:
    assert salon.id is not None
    count = confirmed_overlap_count(
        session, salon.id, start_at, end_at, exclude_booking_id=exclude_booking_id
    )
    return count < salon.chairs


def _windows_for(session: Session, salon_id: int, weekday: int) -> list[SalonAvailability]:
    return list(
        session.exec(
            select(SalonAvailability).where(
                SalonAvailability.salon_id == salon_id,
                SalonAvailability.day_of_week == weekday,
            )
        )
    )


def _within_hours(session: Session, salon_id: int, start_at: datetime, end_at: datetime) -> bool:
    return any(
        w.start_time <= start_at.time() and end_at.time() <= w.end_time
        for w in _windows_for(session, salon_id, start_at.weekday())
    )


def available_slots(
    session: Session,
    salon_id: int,
    service_id: int,
    on_date: date,
    *,
    now: datetime | None = None,
) -> list[datetime]:
    """Bookable start times: inside a working window and with spare capacity."""
    salon = get_salon(session, salon_id)
    service = get_service(session, service_id, salon_id)
    duration = timedelta(minutes=service.duration_minutes)
    step = timedelta(minutes=SLOT_STEP_MINUTES)

    slots: list[datetime] = []
    for window in _windows_for(session, salon_id, on_date.weekday()):
        start = datetime.combine(on_date, window.start_time)
        window_end = datetime.combine(on_date, window.end_time)
        while start + duration <= window_end:
            end = start + duration
            future = now is None or start > now
            if future and has_capacity(session, salon, start, end):
                slots.append(start)
            start += step
    return slots


# --- booking lifecycle ---------------------------------------------------


def request_booking(
    session: Session,
    *,
    client_id: int,
    salon_id: int,
    service_id: int,
    start_at: datetime,
    look_style_id: str | None = None,
) -> Booking:
    """Create a pending booking request, validating hours + spare capacity."""
    salon = get_salon(session, salon_id)
    service = get_service(session, service_id, salon_id)
    end_at = start_at + timedelta(minutes=service.duration_minutes)

    if not _within_hours(session, salon_id, start_at, end_at):
        raise BookingError("That time is outside the salon's opening hours.")
    if not has_capacity(session, salon, start_at, end_at):
        raise BookingError("That slot is already fully booked. Please pick another time.")

    booking = Booking(
        client_id=client_id,
        salon_id=salon_id,
        service_id=service_id,
        start_at=start_at,
        end_at=end_at,
        look_style_id=look_style_id,
        status=PENDING,
    )
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return booking


def _owned_booking(session: Session, booking_id: int, owner_id: int) -> Booking:
    booking = session.get(Booking, booking_id)
    if booking is None:
        raise BookingError("Booking not found.")
    salon = session.get(Salon, booking.salon_id)
    if salon is None or salon.owner_id != owner_id:
        raise BookingError("You don't manage that booking.")
    return booking


def accept_booking(session: Session, owner_id: int, booking_id: int) -> Booking:
    """Salon owner accepts a pending request (re-checking capacity)."""
    booking = _owned_booking(session, booking_id, owner_id)
    if booking.status != PENDING:
        raise BookingError("Only pending requests can be accepted.")
    salon = session.get(Salon, booking.salon_id)
    assert salon is not None
    if not has_capacity(
        session, salon, booking.start_at, booking.end_at, exclude_booking_id=booking.id
    ):
        raise BookingError("That slot is now full — decline and suggest another time.")
    booking.status = CONFIRMED
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return booking


def decline_booking(
    session: Session,
    owner_id: int,
    booking_id: int,
    *,
    suggested_start_at: datetime | None = None,
) -> Booking:
    """Salon owner declines a request, optionally suggesting a new time."""
    booking = _owned_booking(session, booking_id, owner_id)
    if booking.status not in (PENDING, CONFIRMED):
        raise BookingError("That booking can't be declined.")
    booking.status = DECLINED
    booking.suggested_start_at = suggested_start_at
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return booking


def cancel_booking(session: Session, client_id: int, booking_id: int) -> Booking:
    """Client cancels their own booking."""
    booking = session.get(Booking, booking_id)
    if booking is None or booking.client_id != client_id:
        raise BookingError("Booking not found.")
    booking.status = CANCELLED
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return booking


def list_client_bookings(session: Session, client_id: int) -> list[Booking]:
    return list(
        session.exec(
            select(Booking)
            .where(Booking.client_id == client_id)
            .order_by(Booking.start_at.desc())  # type: ignore[attr-defined]
        )
    )


def list_salon_bookings(
    session: Session, salon_id: int, *, status: str | None = None
) -> list[Booking]:
    stmt = select(Booking).where(Booking.salon_id == salon_id)
    if status:
        stmt = stmt.where(Booking.status == status)
    return list(session.exec(stmt.order_by(Booking.start_at)))  # type: ignore[arg-type]


def salon_stats(session: Session, salon_id: int, now: datetime) -> dict[str, int]:
    """Dashboard metrics: requests, upcoming, completed, revenue, clients."""
    bookings = list(session.exec(select(Booking).where(Booking.salon_id == salon_id)))
    confirmed = [b for b in bookings if b.status == CONFIRMED]
    revenue = 0
    for b in confirmed:
        service = session.get(Service, b.service_id)
        if service is not None:
            revenue += service.price_pennies
    return {
        "pending_requests": sum(1 for b in bookings if b.status == PENDING),
        "upcoming_confirmed": sum(1 for b in confirmed if b.start_at > now),
        "completed": sum(1 for b in confirmed if b.end_at <= now),
        "revenue_pennies": revenue,
        "unique_clients": len({b.client_id for b in bookings if b.status != CANCELLED}),
    }
