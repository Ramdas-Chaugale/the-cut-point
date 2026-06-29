"""Booking API: salon discovery, availability, and the request/approve flow."""

from __future__ import annotations

from datetime import date as date_type
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.api.deps import require_client, require_saloon
from app.core.db import get_session
from app.models.booking import (
    BookingDetail,
    BookingRead,
    BookingRequest,
    DeclineRequest,
    SalonDetail,
    SalonRead,
    SalonStats,
    ServiceRead,
    SlotsResponse,
)
from app.models.tables import Salon, Service, User
from app.services import booking as svc

router = APIRouter(prefix="/api", tags=["booking"])


# --- helpers -------------------------------------------------------------


def _owner_salon_id(session: Session, owner: User) -> int:
    salon = session.exec(select(Salon).where(Salon.owner_id == owner.id)).first()
    if salon is None or salon.id is None:
        raise HTTPException(status_code=404, detail="No salon for this account.")
    return salon.id


def _detail(session: Session, booking_obj: object) -> BookingDetail:
    b = booking_obj  # a Booking
    service = session.get(Service, b.service_id)  # type: ignore[attr-defined]
    salon = session.get(Salon, b.salon_id)  # type: ignore[attr-defined]
    client = session.get(User, b.client_id)  # type: ignore[attr-defined]
    base = BookingRead.model_validate(b).model_dump()
    return BookingDetail(
        **base,
        service_name=service.name if service else "",
        salon_name=salon.name if salon else "",
        client_name=client.full_name if client else "",
        price_pennies=service.price_pennies if service else 0,
    )


# --- discovery (public) --------------------------------------------------


@router.get("/salons", response_model=list[SalonRead])
def list_salons(
    city: str | None = Query(default=None),
    session: Session = Depends(get_session),
) -> list[SalonRead]:
    return [SalonRead.model_validate(s) for s in svc.list_salons(session, city=city)]


@router.get("/salons/{salon_id}", response_model=SalonDetail)
def salon_detail(salon_id: int, session: Session = Depends(get_session)) -> SalonDetail:
    try:
        salon = svc.get_salon(session, salon_id)
    except svc.BookingError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    services = [ServiceRead.model_validate(s) for s in svc.list_services(session, salon_id)]
    return SalonDetail(**SalonRead.model_validate(salon).model_dump(), services=services)


@router.get("/salons/{salon_id}/availability", response_model=SlotsResponse)
def availability(
    salon_id: int,
    service_id: int = Query(...),
    on_date: date_type = Query(..., alias="date"),
    session: Session = Depends(get_session),
) -> SlotsResponse:
    try:
        slots = svc.available_slots(session, salon_id, service_id, on_date, now=datetime.now())
    except svc.BookingError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return SlotsResponse(salon_id=salon_id, service_id=service_id, date=on_date, slots=slots)


# --- client booking flow -------------------------------------------------


@router.post("/bookings", response_model=BookingDetail)
def request_booking(
    payload: BookingRequest,
    client: User = Depends(require_client),
    session: Session = Depends(get_session),
) -> BookingDetail:
    try:
        booking = svc.request_booking(
            session,
            client_id=client.id,  # type: ignore[arg-type]
            salon_id=payload.salon_id,
            service_id=payload.service_id,
            start_at=payload.start_at,
            look_style_id=payload.look_style_id,
        )
    except svc.BookingError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return _detail(session, booking)


@router.get("/bookings/me", response_model=list[BookingDetail])
def my_bookings(
    client: User = Depends(require_client),
    session: Session = Depends(get_session),
) -> list[BookingDetail]:
    return [_detail(session, b) for b in svc.list_client_bookings(session, client.id)]  # type: ignore[arg-type]


@router.post("/bookings/{booking_id}/cancel", response_model=BookingDetail)
def cancel_booking(
    booking_id: int,
    client: User = Depends(require_client),
    session: Session = Depends(get_session),
) -> BookingDetail:
    try:
        booking = svc.cancel_booking(session, client.id, booking_id)  # type: ignore[arg-type]
    except svc.BookingError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _detail(session, booking)


# --- saloon (owner) flow -------------------------------------------------


@router.get("/salon/bookings", response_model=list[BookingDetail])
def salon_bookings(
    booking_status: str | None = Query(default=None, alias="status"),
    owner: User = Depends(require_saloon),
    session: Session = Depends(get_session),
) -> list[BookingDetail]:
    salon_id = _owner_salon_id(session, owner)
    bookings = svc.list_salon_bookings(session, salon_id, status=booking_status)
    return [_detail(session, b) for b in bookings]


@router.get("/salon/stats", response_model=SalonStats)
def salon_statistics(
    owner: User = Depends(require_saloon),
    session: Session = Depends(get_session),
) -> SalonStats:
    salon_id = _owner_salon_id(session, owner)
    return SalonStats(**svc.salon_stats(session, salon_id, datetime.now()))


@router.post("/bookings/{booking_id}/accept", response_model=BookingDetail)
def accept_booking(
    booking_id: int,
    owner: User = Depends(require_saloon),
    session: Session = Depends(get_session),
) -> BookingDetail:
    try:
        booking = svc.accept_booking(session, owner.id, booking_id)  # type: ignore[arg-type]
    except svc.BookingError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return _detail(session, booking)


@router.post("/bookings/{booking_id}/decline", response_model=BookingDetail)
def decline_booking(
    booking_id: int,
    payload: DeclineRequest,
    owner: User = Depends(require_saloon),
    session: Session = Depends(get_session),
) -> BookingDetail:
    try:
        booking = svc.decline_booking(
            session,
            owner.id,  # type: ignore[arg-type]
            booking_id,
            suggested_start_at=payload.suggested_start_at,
        )
    except svc.BookingError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _detail(session, booking)
