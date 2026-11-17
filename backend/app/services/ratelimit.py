"""Fixed-window rate limiting, counted in Postgres.

The obvious implementation is a dict in memory. That does not work here. Each
serverless invocation can get a fresh container, so an in-memory counter starts
at zero for most requests and protects nothing. The limit has to live somewhere
both invocations can see, and the database is already there.

One row per caller per window. The increment is a single INSERT ... ON CONFLICT
DO UPDATE, so two requests arriving together cannot both read 4 and both write
5: Postgres serialises them on the primary key and each gets its own number
back.

This guards spend, not abuse. A determined caller changes IP. What it stops is
one person, or one script, quietly emptying a credit balance.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from fastapi import Request
from sqlalchemy import text
from sqlmodel import Session


@dataclass(frozen=True)
class Decision:
    allowed: bool
    remaining: int
    limit: int
    retry_after: int  # seconds until the window rolls over


def client_key(request: Request) -> str:
    """Who is calling, as well as a proxy can tell.

    Vercel terminates TLS and forwards the caller in x-forwarded-for, leftmost
    entry. Trusting that header is only safe behind a proxy that overwrites it,
    which is the case here; direct to the app it would be spoofable.
    """
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _window_start(now: datetime, seconds: int) -> datetime:
    epoch = int(now.timestamp())
    return datetime.fromtimestamp(epoch - (epoch % seconds), tz=UTC)


def check(session: Session, bucket: str, key: str, limit: int,
          window_seconds: int) -> Decision:
    """Count this request and say whether it is over the limit."""
    now = datetime.now(UTC)
    start = _window_start(now, window_seconds)

    row = session.exec(  # type: ignore[call-overload]
        text(
            """
            INSERT INTO rate_limits (bucket, client_key, window_start, hits)
            VALUES (:bucket, :key, :start, 1)
            ON CONFLICT (bucket, client_key, window_start)
            DO UPDATE SET hits = rate_limits.hits + 1
            RETURNING hits
            """
        ),
        params={"bucket": bucket, "key": key, "start": start},
    ).one()
    session.commit()

    hits = int(row[0])
    resets_at = start + timedelta(seconds=window_seconds)
    return Decision(
        allowed=hits <= limit,
        remaining=max(limit - hits, 0),
        limit=limit,
        retry_after=max(int((resets_at - now).total_seconds()), 1),
    )


def sweep(session: Session, older_than_seconds: int = 86_400) -> int:
    """Drop windows nobody will read again, so the table stays small."""
    cutoff = datetime.now(UTC) - timedelta(seconds=older_than_seconds)
    result = session.exec(  # type: ignore[call-overload]
        text("DELETE FROM rate_limits WHERE window_start < :cutoff"),
        params={"cutoff": cutoff},
    )
    session.commit()
    return result.rowcount or 0
