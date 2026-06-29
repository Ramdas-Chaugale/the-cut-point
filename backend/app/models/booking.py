"""API schemas for the booking domain (salons, services, slots, bookings)."""

from __future__ import annotations

from datetime import date as date_type
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ServiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    salon_id: int
    name: str
    description: str
    duration_minutes: int
    price_pennies: int


class SalonRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    address: str
    city: str
    latitude: float
    longitude: float
    phone: str
    photo_url: str | None
    chairs: int


class SalonWithDistance(SalonRead):
    distance_km: float | None = None


class SalonDetail(SalonRead):
    services: list[ServiceRead]


class SlotsResponse(BaseModel):
    salon_id: int
    service_id: int
    date: date_type
    slots: list[datetime]


class BookingRequest(BaseModel):
    salon_id: int
    service_id: int
    start_at: datetime
    look_style_id: str | None = None


class DeclineRequest(BaseModel):
    suggested_start_at: datetime | None = None


class BookingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    salon_id: int
    service_id: int
    start_at: datetime
    end_at: datetime
    status: str
    look_style_id: str | None
    suggested_start_at: datetime | None


class SalonStats(BaseModel):
    pending_requests: int
    upcoming_confirmed: int
    completed: int
    revenue_pennies: int
    unique_clients: int


class BookingDetail(BookingRead):
    """A booking enriched with the names the dashboards display."""

    service_name: str
    salon_name: str
    client_name: str = ""
    price_pennies: int = Field(default=0)
