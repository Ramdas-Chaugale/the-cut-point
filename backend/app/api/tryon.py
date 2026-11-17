"""Realistic AI try-on API router."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlmodel import Session

from app.core.config import get_settings
from app.core.db import get_session
from app.models.tryon import TryOnRequest, TryOnResponse
from app.services import ratelimit
from app.services import tryon as svc

router = APIRouter(prefix="/api/tryon", tags=["tryon"])

# Every call here spends money or free-tier quota at an image provider, and the
# endpoint is public. The limit is per caller per hour, low enough that trying a
# few styles is comfortable and a script is not.
TRYON_LIMIT = 10
TRYON_WINDOW_SECONDS = 3600


def enforce_tryon_limit(
    request: Request,
    response: Response,
    session: Session = Depends(get_session),
) -> None:
    """Count the call and reject it if the caller is over the limit.

    A dependency rather than middleware, so it only guards the route that
    actually costs something, and so it runs before the provider is touched.
    """
    decision = ratelimit.check(
        session,
        bucket="tryon",
        key=ratelimit.client_key(request),
        limit=TRYON_LIMIT,
        window_seconds=TRYON_WINDOW_SECONDS,
    )

    response.headers["X-RateLimit-Limit"] = str(decision.limit)
    response.headers["X-RateLimit-Remaining"] = str(decision.remaining)

    if not decision.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Try-on is limited to {decision.limit} images per hour. "
                f"Try again in {decision.retry_after // 60 + 1} minutes."
            ),
            headers={
                "Retry-After": str(decision.retry_after),
                "X-RateLimit-Limit": str(decision.limit),
                "X-RateLimit-Remaining": "0",
            },
        )


@router.post(
    "/generate",
    response_model=TryOnResponse,
    dependencies=[Depends(enforce_tryon_limit)],
)
def generate(payload: TryOnRequest) -> TryOnResponse:
    """Generate a photorealistic image of the user wearing the chosen style."""
    try:
        url = svc.generate_tryon(payload.image_data_url, payload.style_id, payload.mask_data_url)
    except svc.TryOnError as exc:
        # 503 when the feature isn't configured; 502 for upstream failures.
        code = (
            status.HTTP_503_SERVICE_UNAVAILABLE
            if "not configured" in str(exc)
            else status.HTTP_502_BAD_GATEWAY
        )
        raise HTTPException(status_code=code, detail=str(exc)) from exc
    return TryOnResponse(image_url=url)


@router.get("/limit", tags=["tryon"])
def limit_info() -> dict:
    """What the limit is, so the interface can say so before someone hits it."""
    return {
        "limit": TRYON_LIMIT,
        "window_seconds": TRYON_WINDOW_SECONDS,
        "enabled": get_settings().ai_tryon_enabled,
    }
