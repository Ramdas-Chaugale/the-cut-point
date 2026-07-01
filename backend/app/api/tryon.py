"""Realistic AI try-on API router."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.models.tryon import TryOnRequest, TryOnResponse
from app.services import tryon as svc

router = APIRouter(prefix="/api/tryon", tags=["tryon"])


@router.post("/generate", response_model=TryOnResponse)
def generate(payload: TryOnRequest) -> TryOnResponse:
    """Generate a photorealistic image of the user wearing the chosen style."""
    try:
        url = svc.generate_tryon(payload.image_data_url, payload.style_id)
    except svc.TryOnError as exc:
        # 503 when the feature isn't configured; 502 for upstream failures.
        code = (
            status.HTTP_503_SERVICE_UNAVAILABLE
            if "not configured" in str(exc)
            else status.HTTP_502_BAD_GATEWAY
        )
        raise HTTPException(status_code=code, detail=str(exc)) from exc
    return TryOnResponse(image_url=url)
