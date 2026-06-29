"""Seed realistic demo data: services, stylists and weekly availability.

Idempotent: running it again when data already exists is a no-op. Run with:
    python -m app.db.seed
"""

from __future__ import annotations

from datetime import time

from sqlmodel import Session, select

from app.core.db import engine
from app.models.tables import Service, Stylist, StylistAvailability

# (name, description, duration_minutes, price_pennies)
SERVICES: list[tuple[str, str, int, int]] = [
    ("Skin Fade", "Sharp clipper fade, blended and finished.", 30, 1800),
    ("Classic Cut", "Scissor cut, wash and style.", 30, 2000),
    ("Cut & Blow Dry", "Consultation, cut, wash and blow-dry.", 60, 4500),
    ("Beard Trim", "Shape-up and tidy with hot towel.", 15, 1000),
    ("Full Head Colour", "Single-process all-over colour.", 120, 8500),
    ("Highlights", "Foil highlights and toner.", 90, 7500),
    ("Kids Cut", "Cut and style for under-12s.", 20, 1200),
]

# (name, bio, [(day_of_week, start, end), ...])  day_of_week: 0=Mon .. 6=Sun
_WEEKDAYS = [(d, time(9, 0), time(17, 0)) for d in range(0, 5)]  # Mon–Fri 9–5
_WITH_SAT = _WEEKDAYS + [(5, time(9, 0), time(13, 0))]  # + Sat morning

STYLISTS: list[tuple[str, str, list[tuple[int, time, time]]]] = [
    ("Alex Rivera", "Senior barber — fades and classic men's cuts.", _WITH_SAT),
    ("Sam Okafor", "Texture and curly-hair specialist.", _WEEKDAYS),
    ("Jordan Bell", "Colour expert — balayage and highlights.", _WITH_SAT),
    ("Priya Shah", "Precision cuts and everyday styling.", _WEEKDAYS),
    ("Chris Doyle", "Beards, fades and hot-towel shaves.", _WITH_SAT),
]


def seed(session: Session) -> bool:
    """Populate demo data. Returns False if the DB was already seeded."""
    if session.exec(select(Service)).first() is not None:
        return False

    for name, desc, dur, price in SERVICES:
        session.add(Service(name=name, description=desc, duration_minutes=dur, price_pennies=price))

    for name, bio, windows in STYLISTS:
        stylist = Stylist(name=name, bio=bio)
        session.add(stylist)
        session.commit()
        session.refresh(stylist)
        for dow, start, end in windows:
            session.add(
                StylistAvailability(
                    stylist_id=stylist.id,
                    day_of_week=dow,
                    start_time=start,
                    end_time=end,
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
