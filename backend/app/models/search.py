"""Schemas for natural-language style search and the stylist assistant."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.recommend import (
    AngleAssets,
    FaceShape,
    HairType,
    Length,
    Maintenance,
    Presentation,
)


class SearchRequest(BaseModel):
    """A free-text description of the haircut someone is after."""

    query: str = Field(min_length=2, max_length=400)
    limit: int = Field(default=8, ge=1, le=28)


class ParsedQuery(BaseModel):
    """What the query was understood to mean, shown back to the user."""

    presentation: Presentation | None = None
    length: Length | None = None
    hair_type: HairType | None = None
    maintenance: Maintenance | None = None
    face_shape: FaceShape | None = None
    summary: list[str]
    source: str  # "llm" | "keywords"


class SearchHitOut(BaseModel):
    """One search result, with the reasons it matched."""

    id: str
    name: str
    length: Length
    maintenance: Maintenance
    presentations: list[Presentation]
    hair_types: list[HairType]
    description: str
    angle_assets: AngleAssets
    try_on_overlay: str
    score: float
    reasons: list[str]


class SearchResponse(BaseModel):
    query: str
    parsed: ParsedQuery
    count: int
    results: list[SearchHitOut]


class AssistantRequest(BaseModel):
    """A styling question, optionally with the client's face shape as context."""

    question: str = Field(min_length=2, max_length=400)
    face_shape: FaceShape | None = None


class AssistantSource(BaseModel):
    """A catalogue entry the answer was drawn from."""

    id: str
    name: str
    description: str


class AssistantResponse(BaseModel):
    answer: str
    sources: list[AssistantSource]
    source: str  # "llm" | "fallback"
