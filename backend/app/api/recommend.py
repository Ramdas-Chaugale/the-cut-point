"""Recommendation API router."""

from __future__ import annotations

from fastapi import APIRouter

from app.models.recommend import RecommendRequest, RecommendResponse
from app.services.recommend import recommend as run_recommend

router = APIRouter(prefix="/api", tags=["recommend"])


@router.post("/recommend", response_model=RecommendResponse)
def recommend(payload: RecommendRequest) -> RecommendResponse:
    """Rank hairstyles for a face shape + user preferences (deterministic)."""
    return run_recommend(payload)
