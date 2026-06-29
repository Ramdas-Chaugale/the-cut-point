"""Schemas + controlled vocabularies for the recommendation engine."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class FaceShape(str, Enum):
    oval = "oval"
    round = "round"
    square = "square"
    oblong = "oblong"
    heart = "heart"
    diamond = "diamond"
    triangle = "triangle"


class Presentation(str, Enum):
    masculine = "masculine"
    feminine = "feminine"
    unisex = "unisex"


class Length(str, Enum):
    short = "short"
    medium = "medium"
    long = "long"


class HairType(str, Enum):
    straight = "straight"
    wavy = "wavy"
    curly = "curly"
    coily = "coily"


class Maintenance(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


# Allowed rationale tags (validated when the knowledge base loads).
RATIONALE_TAGS: frozenset[str] = frozenset(
    {
        "adds-height",
        "elongates",
        "softens-angles",
        "adds-width",
        "balances-forehead",
        "balances-jaw",
        "frames-face",
        "highlights-bone-structure",
        "adds-texture",
        "adds-volume",
        "low-upkeep",
        "shortens-face",
    }
)


class Style(BaseModel):
    """A single hairstyle in the knowledge base."""

    id: str
    name: str
    presentations: list[Presentation]
    length: Length
    hair_types: list[HairType]
    maintenance: Maintenance
    flattering_for: list[FaceShape]
    rationale_tags: list[str]
    description: str


class RecommendRequest(BaseModel):
    """User inputs. Optional fields left unset mean 'no preference'."""

    face_shape: FaceShape
    presentation: Presentation | None = None
    desired_length: Length | None = None
    hair_type: HairType | None = None
    maintenance: Maintenance | None = None
    limit: int = Field(default=8, ge=1, le=28)


class StyleRecommendation(BaseModel):
    """One ranked recommendation returned to the client."""

    id: str
    name: str
    length: Length
    maintenance: Maintenance
    presentations: list[Presentation]
    hair_types: list[HairType]
    rationale_tags: list[str]
    description: str
    match_score: float  # 0..1, how well it fits the requested inputs
    matched_on: list[str]  # which preferences this style satisfied
    explanation: str  # rule-based "why it suits you" (LLM-enriched in Phase 4)


class RecommendResponse(BaseModel):
    face_shape: FaceShape
    count: int
    recommendations: list[StyleRecommendation]
