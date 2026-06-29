"""API schemas for the booking domain (read models + request bodies)."""

from __future__ import annotations

from datetime import date as date_type
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ServiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    duration_minutes: int
    price_pennies: int


class StylistRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    bio: str


class SlotsResponse(BaseModel):
    stylist_id: int
    service_id: int
    date: date_type
    slots: list[datetime]


class BookingCreate(BaseModel):
    """Request body for creating a booking (used from Phase 7 with auth)."""

    stylist_id: int
    service_id: int
    start_at: datetime
    look_style_id: str | None = None


class BookingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    stylist_id: int
    service_id: int
    start_at: datetime
    end_at: datetime
    status: str
    look_style_id: str | None
