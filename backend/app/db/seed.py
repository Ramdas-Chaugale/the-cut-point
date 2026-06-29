"""Seed realistic demo data: barber accounts + their salons, services,
availability, and a demo client.

Idempotent. Run with:  python -m app.db.seed

Demo logins (password for all: "password123"):
  client@cutpoint.demo                 — a client account
  alex@cutpoint.demo .. chris@...       — saloon (barber) accounts
"""

from __future__ import annotations

from datetime import time

from sqlmodel import Session, select

from app.core.db import engine
from app.core.security import hash_password
from app.models.tables import Salon, SalonAvailability, Service, User

DEMO_PASSWORD = "password123"

# Service templates: (name, description, duration_minutes, price_pennies)
SVC = {
    "skin_fade": ("Skin Fade", "Sharp clipper fade, blended and finished.", 30, 1800),
    "classic": ("Classic Cut", "Scissor cut, wash and style.", 30, 2000),
    "cbd": ("Cut & Blow Dry", "Consultation, cut, wash and blow-dry.", 60, 4500),
    "beard": ("Beard Trim", "Shape-up and tidy with hot towel.", 15, 1000),
    "colour": ("Full Head Colour", "Single-process all-over colour.", 120, 8500),
    "highlights": ("Highlights", "Foil highlights and toner.", 90, 7500),
    "kids": ("Kids Cut", "Cut and style for under-12s.", 20, 1200),
}

_MON_FRI = [(d, time(9, 0), time(17, 0)) for d in range(5)]
_MON_SAT = _MON_FRI + [(5, time(9, 0), time(13, 0))]

# (owner full name, email, salon fields, service keys, availability, chairs)
SALONS = [
    (
        "Alex Rivera",
        "alex@cutpoint.demo",
        {
            "name": "Sharp Fades Barbers",
            "description": "East-London barbershop specialising in fades and classic men's cuts.",
            "address": "12 Curtain Road, Shoreditch",
            "city": "London",
            "latitude": 51.5265,
            "longitude": -0.0780,
            "phone": "020 7000 1001",
        },
        ["skin_fade", "classic", "beard", "kids"],
        _MON_SAT,
        3,
    ),
    (
        "Sam Okafor",
        "sam@cutpoint.demo",
        {
            "name": "Curl & Co",
            "description": "Texture and curly-hair specialists in the heart of Brixton.",
            "address": "48 Atlantic Road, Brixton",
            "city": "London",
            "latitude": 51.4613,
            "longitude": -0.1156,
            "phone": "020 7000 1002",
        },
        ["cbd", "classic", "highlights"],
        _MON_FRI,
        2,
    ),
    (
        "Jordan Bell",
        "jordan@cutpoint.demo",
        {
            "name": "Colour Lounge",
            "description": "Colour studio — balayage, highlights and full-head colour.",
            "address": "7 Greek Street, Soho",
            "city": "London",
            "latitude": 51.5138,
            "longitude": -0.1340,
            "phone": "020 7000 1003",
        },
        ["cbd", "colour", "highlights"],
        _MON_SAT,
        2,
    ),
    (
        "Priya Shah",
        "priya@cutpoint.demo",
        {
            "name": "Precision Studio",
            "description": "Precision cuts and everyday styling in Camden.",
            "address": "21 Camden High Street, Camden",
            "city": "London",
            "latitude": 51.5390,
            "longitude": -0.1426,
            "phone": "020 7000 1004",
        },
        ["cbd", "classic", "kids"],
        _MON_FRI,
        2,
    ),
    (
        "Chris Doyle",
        "chris@cutpoint.demo",
        {
            "name": "The Gents Room",
            "description": "Beards, fades and hot-towel shaves in Islington.",
            "address": "3 Upper Street, Islington",
            "city": "London",
            "latitude": 51.5362,
            "longitude": -0.1033,
            "phone": "020 7000 1005",
        },
        ["skin_fade", "classic", "beard"],
        _MON_SAT,
        3,
    ),
]


def seed(session: Session) -> bool:
    """Populate demo data. Returns False if already seeded."""
    if session.exec(select(User)).first() is not None:
        return False

    # Demo client.
    session.add(
        User(
            email="client@cutpoint.demo",
            hashed_password=hash_password(DEMO_PASSWORD),
            full_name="Jamie Client",
            role="client",
            phone="07700 900000",
        )
    )
    session.commit()

    for owner_name, email, salon_fields, service_keys, windows, chairs in SALONS:
        owner = User(
            email=email,
            hashed_password=hash_password(DEMO_PASSWORD),
            full_name=owner_name,
            role="saloon",
        )
        session.add(owner)
        session.commit()
        session.refresh(owner)

        salon = Salon(owner_id=owner.id, chairs=chairs, **salon_fields)
        session.add(salon)
        session.commit()
        session.refresh(salon)

        for key in service_keys:
            name, desc, dur, price = SVC[key]
            session.add(
                Service(
                    salon_id=salon.id,
                    name=name,
                    description=desc,
                    duration_minutes=dur,
                    price_pennies=price,
                )
            )
        for dow, start, end in windows:
            session.add(
                SalonAvailability(
                    salon_id=salon.id, day_of_week=dow, start_time=start, end_time=end
                )
            )
        session.commit()
    return True


def main() -> None:
    with Session(engine) as session:
        created = seed(session)
    print("Seeded demo data." if created else "Demo data already present; nothing to do.")


if __name__ == "__main__":
    main()
