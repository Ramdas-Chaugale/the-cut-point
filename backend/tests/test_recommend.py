"""Tests for the deterministic recommendation engine."""

from __future__ import annotations

from app.knowledge.loader import load_styles
from app.models.recommend import (
    FaceShape,
    HairType,
    Length,
    Maintenance,
    Presentation,
    RecommendRequest,
)
from app.services.recommend import recommend


def _ids(req: RecommendRequest) -> list[str]:
    return [r.id for r in recommend(req).recommendations]


# --- Core guarantees -----------------------------------------------------


def test_is_deterministic() -> None:
    req = RecommendRequest(
        face_shape=FaceShape.heart,
        presentation=Presentation.feminine,
        desired_length=Length.medium,
        hair_type=HairType.wavy,
        maintenance=Maintenance.low,
    )
    first = recommend(req).model_dump()
    second = recommend(req).model_dump()
    assert first == second


def test_only_flattering_styles_returned() -> None:
    for shape in FaceShape:
        kb = {s.id: s for s in load_styles()}
        for rec in recommend(RecommendRequest(face_shape=shape)).recommendations:
            assert shape in kb[rec.id].flattering_for


def test_scores_in_range_and_sorted_descending() -> None:
    recs = recommend(
        RecommendRequest(face_shape=FaceShape.oval, desired_length=Length.short)
    ).recommendations
    scores = [r.match_score for r in recs]
    assert all(0.0 <= s <= 1.0 for s in scores)
    assert scores == sorted(scores, reverse=True)


def test_limit_is_respected() -> None:
    recs = recommend(RecommendRequest(face_shape=FaceShape.oval, limit=3)).recommendations
    assert len(recs) == 3


# --- Inputs change outputs sensibly --------------------------------------


def test_face_shape_changes_the_result_set() -> None:
    oval = set(_ids(RecommendRequest(face_shape=FaceShape.oval)))
    triangle = set(_ids(RecommendRequest(face_shape=FaceShape.triangle)))
    assert oval != triangle


def test_desired_length_reorders_results() -> None:
    short = _ids(RecommendRequest(face_shape=FaceShape.round, desired_length=Length.short))
    long_ = _ids(RecommendRequest(face_shape=FaceShape.round, desired_length=Length.long))
    assert short != long_
    # The top short pick should actually be a short style.
    kb = {s.id: s for s in load_styles()}
    assert kb[short[0]].length == Length.short
    assert kb[long_[0]].length == Length.long


def test_hair_type_changes_scores() -> None:
    straight = recommend(
        RecommendRequest(face_shape=FaceShape.square, hair_type=HairType.straight)
    ).recommendations
    coily = recommend(
        RecommendRequest(face_shape=FaceShape.square, hair_type=HairType.coily)
    ).recommendations
    assert {r.id: r.match_score for r in straight} != {r.id: r.match_score for r in coily}


def test_no_preferences_returns_full_flattering_set_at_score_one() -> None:
    recs = recommend(RecommendRequest(face_shape=FaceShape.oval, limit=28)).recommendations
    assert len(recs) >= 4
    assert all(r.match_score == 1.0 for r in recs)


# --- Presentation filtering ----------------------------------------------


def test_masculine_only_style_excluded_for_feminine_request() -> None:
    # Pompadour is masculine-only and flatters round faces.
    feminine = _ids(
        RecommendRequest(face_shape=FaceShape.round, presentation=Presentation.feminine)
    )
    assert "pompadour" not in feminine


def test_unisex_request_excludes_gendered_only_styles() -> None:
    unisex = _ids(RecommendRequest(face_shape=FaceShape.round, presentation=Presentation.unisex))
    kb = {s.id: s for s in load_styles()}
    for sid in unisex:
        assert Presentation.unisex in kb[sid].presentations


def test_unisex_styles_appear_for_every_presentation() -> None:
    # Wavy Curtains is unisex and flatters round; it should appear for all.
    for pres in Presentation:
        ids = _ids(RecommendRequest(face_shape=FaceShape.round, presentation=pres, limit=28))
        assert "wavy-curtain" in ids


def test_explanation_mentions_the_style_and_shape() -> None:
    rec = recommend(RecommendRequest(face_shape=FaceShape.square)).recommendations[0]
    assert rec.name in rec.explanation
    assert "square" in rec.explanation
