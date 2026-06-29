"""Booking API router — read endpoints (services, stylists, availability).

Booking create/cancel/list endpoints are added in Phase 7, wired to the
authenticated user.
"""

from __future__ import annotations

from datetime import date as date_type
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.core.db import get_session
from app.models.booking import ServiceRead, SlotsResponse, StylistRead
from app.services import booking as svc

router = APIRouter(prefix="/api", tags=["booking"])


@router.get("/services", response_model=list[ServiceRead])
def get_services(session: Session = Depends(get_session)) -> list[ServiceRead]:
    return [ServiceRead.model_validate(s) for s in svc.list_services(session)]


@router.get("/stylists", response_model=list[StylistRead])
def get_stylists(session: Session = Depends(get_session)) -> list[StylistRead]:
    return [StylistRead.model_validate(s) for s in svc.list_stylists(session)]


@router.get("/availability", response_model=SlotsResponse)
def get_availability(
    stylist_id: int = Query(...),
    service_id: int = Query(...),
    on_date: date_type = Query(..., alias="date"),
    session: Session = Depends(get_session),
) -> SlotsResponse:
    """Bookable start times for a stylist+service on a date (past slots dropped)."""
    try:
        slots = svc.available_slots(session, stylist_id, service_id, on_date, now=datetime.now())
    except svc.BookingError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return SlotsResponse(stylist_id=stylist_id, service_id=service_id, date=on_date, slots=slots)
