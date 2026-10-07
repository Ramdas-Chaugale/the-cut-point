"""Natural-language search and stylist assistant router."""

from __future__ import annotations

from fastapi import APIRouter

from app.knowledge.loader import load_styles
from app.models.search import (
    AssistantRequest,
    AssistantResponse,
    AssistantSource,
    ParsedQuery,
    SearchHitOut,
    SearchRequest,
    SearchResponse,
)
from app.services.assets import angle_assets, overlay_url
from app.services.assistant import ask as run_ask
from app.services.style_search import search as run_search

router = APIRouter(prefix="/api", tags=["search"])


@router.post("/search", response_model=SearchResponse)
def search(payload: SearchRequest) -> SearchResponse:
    """Rank the catalogue against a free-text description of what someone wants."""
    constraints, hits = run_search(payload.query, limit=payload.limit)

    parsed = ParsedQuery(
        presentation=constraints.presentation,
        length=constraints.length,
        hair_type=constraints.hair_type,
        maintenance=constraints.maintenance,
        face_shape=constraints.face_shape,
        summary=constraints.describe(),
        source=constraints.source,
    )
    results = [
        SearchHitOut(
            id=h.style.id,
            name=h.style.name,
            length=h.style.length,
            maintenance=h.style.maintenance,
            presentations=h.style.presentations,
            hair_types=h.style.hair_types,
            description=h.style.description,
            angle_assets=angle_assets(h.style.id),
            try_on_overlay=overlay_url(h.style.id),
            score=h.score,
            reasons=h.reasons,
        )
        for h in hits
    ]
    return SearchResponse(query=payload.query, parsed=parsed, count=len(results), results=results)


@router.post("/assistant", response_model=AssistantResponse)
def assistant(payload: AssistantRequest) -> AssistantResponse:
    """Answer a styling question using only the catalogue, citing what it used."""
    result = run_ask(payload.question, payload.face_shape)
    return AssistantResponse(
        answer=result.text,
        sources=[
            AssistantSource(id=s.id, name=s.name, description=s.description) for s in result.sources
        ],
        source=result.source,
    )


@router.get("/styles", response_model=list[SearchHitOut])
def styles() -> list[SearchHitOut]:
    """The whole catalogue, for browsing without running a face analysis first."""
    return [
        SearchHitOut(
            id=s.id,
            name=s.name,
            length=s.length,
            maintenance=s.maintenance,
            presentations=s.presentations,
            hair_types=s.hair_types,
            description=s.description,
            angle_assets=angle_assets(s.id),
            try_on_overlay=overlay_url(s.id),
            score=1.0,
            reasons=[],
        )
        for s in load_styles()
    ]
