"""SQLModel database tables.

Two roles share the ``users`` table (``role`` = "client" | "saloon"). A saloon
user owns one ``Salon`` (its shop: location, photos, menu, working windows and
chair count). Clients request bookings against a salon; the salon owner accepts
or declines (optionally suggesting a new time). Times are naive datetimes in the
salon's local timezone (single-region assumption, kept simple for the demo).
"""

from __future__ import annotations

from datetime import datetime, time

from sqlmodel import Field, SQLModel

# Booking lifecycle statuses.
PENDING = "pending"
CONFIRMED = "confirmed"
DECLINED = "declined"
CANCELLED = "cancelled"


def _now() -> datetime:
    """Naive local timestamp (single-salon-timezone assumption)."""
    return datetime.now()


class User(SQLModel, table=True):
    __tablename__ = "users"  # avoid the reserved word "user" in Postgres

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    full_name: str
    role: str  # "client" | "saloon"
    phone: str | None = None
    created_at: datetime = Field(default_factory=_now)


class Salon(SQLModel, table=True):
    __tablename__ = "salons"

    id: int | None = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="users.id", unique=True, index=True)
    name: str
    description: str
    address: str
    city: str = Field(index=True)
    latitude: float
    longitude: float
    phone: str
    photo_url: str | None = None
    chairs: int = 1  # how many clients can be served at once
    created_at: datetime = Field(default_factory=_now)


class Service(SQLModel, table=True):
    __tablename__ = "services"

    id: int | None = Field(default=None, primary_key=True)
    salon_id: int = Field(foreign_key="salons.id", index=True)
    name: str
    description: str
    duration_minutes: int
    price_pennies: int
    active: bool = True


class SalonAvailability(SQLModel, table=True):
    __tablename__ = "salon_availability"

    id: int | None = Field(default=None, primary_key=True)
    salon_id: int = Field(foreign_key="salons.id", index=True)
    day_of_week: int  # 0 = Monday ... 6 = Sunday
    start_time: time
    end_time: time


class Booking(SQLModel, table=True):
    __tablename__ = "bookings"

    id: int | None = Field(default=None, primary_key=True)
    client_id: int = Field(foreign_key="users.id", index=True)
    salon_id: int = Field(foreign_key="salons.id", index=True)
    service_id: int = Field(foreign_key="services.id")
    start_at: datetime = Field(index=True)
    end_at: datetime
    status: str = Field(default=PENDING)  # pending|confirmed|declined|cancelled
    # Optional "bring this look" link to a recommended style id.
    look_style_id: str | None = Field(default=None)
    # Set when the salon declines and proposes another time.
    suggested_start_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=_now)
