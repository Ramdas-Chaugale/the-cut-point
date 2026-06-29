"""Recommendation API router."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.knowledge.loader import load_styles
from app.models.recommend import (
    ExplainRequest,
    ExplainResponse,
    RecommendRequest,
    RecommendResponse,
)
from app.services.llm import generate_explanation
from app.services.recommend import recommend as run_recommend

router = APIRouter(prefix="/api", tags=["recommend"])


@router.post("/recommend", response_model=RecommendResponse)
def recommend(payload: RecommendRequest) -> RecommendResponse:
    """Rank hairstyles for a face shape + user preferences (deterministic)."""
    return run_recommend(payload)


@router.post("/explain", response_model=ExplainResponse)
def explain(payload: ExplainRequest) -> ExplainResponse:
    """LLM-enriched 'why it suits you' for one style (falls back gracefully)."""
    styles = {s.id: s for s in load_styles()}
    style = styles.get(payload.style_id)
    if style is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown style id: {payload.style_id}",
        )
    result = generate_explanation(
        style,
        payload.face_shape,
        presentation=payload.presentation,
        desired_length=payload.desired_length,
        hair_type=payload.hair_type,
        maintenance=payload.maintenance,
    )
    return ExplainResponse(
        style_id=style.id,
        explanation=result.text,
        source=result.source,
        cached=result.cached,
    )
