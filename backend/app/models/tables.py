"""SQLModel database tables for the salon-booking domain.

Times are stored as naive datetimes in the salon's local timezone (a single-
salon assumption, kept simple for the demo). `StylistAvailability` describes a
stylist's weekly working windows; bookable slots are derived from those windows
minus existing bookings (see services/booking.py).
"""

from __future__ import annotations

from datetime import datetime, time

from sqlmodel import Field, SQLModel


def _now() -> datetime:
    """Naive local timestamp (single-salon timezone assumption)."""
    return datetime.now()


class User(SQLModel, table=True):
    __tablename__ = "users"  # avoid the reserved word "user" in Postgres

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    full_name: str
    created_at: datetime = Field(default_factory=_now)


class Service(SQLModel, table=True):
    __tablename__ = "services"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    description: str
    duration_minutes: int
    price_pennies: int
    active: bool = True


class Stylist(SQLModel, table=True):
    __tablename__ = "stylists"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    bio: str
    active: bool = True


class StylistAvailability(SQLModel, table=True):
    __tablename__ = "stylist_availability"

    id: int | None = Field(default=None, primary_key=True)
    stylist_id: int = Field(foreign_key="stylists.id", index=True)
    day_of_week: int  # 0 = Monday ... 6 = Sunday
    start_time: time
    end_time: time


class Booking(SQLModel, table=True):
    __tablename__ = "bookings"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    stylist_id: int = Field(foreign_key="stylists.id", index=True)
    service_id: int = Field(foreign_key="services.id")
    start_at: datetime = Field(index=True)
    end_at: datetime
    status: str = Field(default="confirmed")  # "confirmed" | "cancelled"
    # Optional "bring this look" link to a recommended style id (Phase 7).
    look_style_id: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=_now)
