"""Deterministic hairstyle recommendation engine.

Pipeline:
1. Hard-filter the knowledge base to styles that flatter the user's face shape.
2. Hard-filter by gender presentation (unisex styles always qualify).
3. Score each remaining style against the user's *stated* preferences
   (length, hair type, maintenance) — unstated preferences don't penalise.
4. Rank by score, breaking ties on style id so output is fully deterministic.

No randomness anywhere: the same request always yields the same ordering.
"""

from __future__ import annotations

from app.knowledge.loader import load_styles
from app.models.recommend import (
    Length,
    Maintenance,
    Presentation,
    RecommendRequest,
    RecommendResponse,
    Style,
    StyleRecommendation,
)
from app.services.explanations import build_rule_based_explanation

# Ordinal scales for "adjacency" scoring.
_LENGTH_ORDER = {Length.short: 0, Length.medium: 1, Length.long: 2}
_MAINT_ORDER = {Maintenance.low: 0, Maintenance.medium: 1, Maintenance.high: 2}

_LENGTH_WEIGHT = 3.0
_HAIR_WEIGHT = 2.0
_MAINT_WEIGHT = 2.0


def _presentation_ok(style: Style, wanted: Presentation | None) -> bool:
    if wanted is None:
        return True
    if Presentation.unisex in style.presentations:
        # Unisex styles suit everyone, including someone seeking unisex looks.
        return True
    return wanted in style.presentations


def _ordinal_fit(a_idx: int, b_idx: int) -> float:
    """1.0 if equal, 0.5 if adjacent, 0.0 if two steps apart."""
    diff = abs(a_idx - b_idx)
    if diff == 0:
        return 1.0
    if diff == 1:
        return 0.5
    return 0.0


def _score(style: Style, req: RecommendRequest) -> tuple[float, list[str]]:
    """Return (match_score in 0..1, list of fully-matched criteria)."""
    earned = 0.0
    possible = 0.0
    matched: list[str] = ["face_shape"]  # guaranteed by the upstream filter

    if req.desired_length is not None:
        possible += _LENGTH_WEIGHT
        fit = _ordinal_fit(_LENGTH_ORDER[style.length], _LENGTH_ORDER[req.desired_length])
        earned += fit * _LENGTH_WEIGHT
        if fit == 1.0:
            matched.append("length")

    if req.hair_type is not None:
        possible += _HAIR_WEIGHT
        if req.hair_type in style.hair_types:
            earned += _HAIR_WEIGHT
            matched.append("hair_type")

    if req.maintenance is not None:
        possible += _MAINT_WEIGHT
        fit = _ordinal_fit(_MAINT_ORDER[style.maintenance], _MAINT_ORDER[req.maintenance])
        earned += fit * _MAINT_WEIGHT
        if fit == 1.0:
            matched.append("maintenance")

    score = 1.0 if possible == 0.0 else earned / possible
    return score, matched


def recommend(req: RecommendRequest) -> RecommendResponse:
    """Produce a ranked, deterministic list of hairstyle recommendations."""
    candidates = [
        style
        for style in load_styles()
        if req.face_shape in style.flattering_for and _presentation_ok(style, req.presentation)
    ]

    scored: list[tuple[float, str, Style, list[str]]] = []
    for style in candidates:
        score, matched = _score(style, req)
        scored.append((score, style.id, style, matched))

    # Highest score first; ties broken by id for stable, deterministic output.
    scored.sort(key=lambda item: (-item[0], item[1]))

    recommendations = [
        StyleRecommendation(
            id=style.id,
            name=style.name,
            length=style.length,
            maintenance=style.maintenance,
            presentations=style.presentations,
            hair_types=style.hair_types,
            rationale_tags=style.rationale_tags,
            description=style.description,
            match_score=round(score, 4),
            matched_on=matched,
            explanation=build_rule_based_explanation(style, req.face_shape),
        )
        for score, _id, style, matched in scored[: req.limit]
    ]

    return RecommendResponse(
        face_shape=req.face_shape,
        count=len(recommendations),
        recommendations=recommendations,
    )
