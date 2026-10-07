"""Tests for natural-language style search."""

from __future__ import annotations

import pytest
from app.core.config import get_settings
from app.models.recommend import HairType, Length, Maintenance, Presentation
from app.services import style_search


@pytest.fixture(autouse=True)
def _llm_off(monkeypatch: pytest.MonkeyPatch) -> None:
    """Default every test to the no-key path, so nothing hits the network."""
    settings = get_settings()
    monkeypatch.setattr(type(settings), "llm_enabled", property(lambda self: False))


# --- retrieval --------------------------------------------------------------


def test_lexical_scores_rank_the_obvious_match_first() -> None:
    scores = style_search.lexical_scores("buzz cut skin fade")
    top = max(scores, key=lambda k: scores[k])
    assert top == "buzz-skin-fade"


def test_lexical_scores_are_empty_for_a_query_of_only_stopwords() -> None:
    assert style_search.lexical_scores("i want the a") == {}


def test_every_style_is_scored() -> None:
    scores = style_search.lexical_scores("short hair")
    assert len(scores) == 21


# --- keyword constraint extraction -----------------------------------------


def test_keywords_read_maintenance_and_hair_type() -> None:
    c = style_search.extract_constraints("something low maintenance for curly hair")
    assert c.maintenance is Maintenance.low
    assert c.hair_type is HairType.curly
    assert c.source == "keywords"


def test_longer_phrase_wins_over_the_bare_word() -> None:
    # "low maintenance" must not be read as length=long via a stray "low".
    c = style_search.extract_constraints("a low maintenance cut")
    assert c.maintenance is Maintenance.low


def test_keywords_read_presentation_and_face_shape() -> None:
    c = style_search.extract_constraints("mens cut for a round face")
    assert c.presentation is Presentation.masculine
    assert c.face_shape.value == "round"


def test_unrelated_query_extracts_nothing() -> None:
    c = style_search.extract_constraints("what is the weather")
    assert c.describe() == []


def test_describe_is_human_readable() -> None:
    c = style_search.extract_constraints("short curly low maintenance")
    assert "short length" in c.describe()
    assert "curly hair" in c.describe()


# --- LLM extraction ---------------------------------------------------------


def test_llm_extraction_is_used_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(type(settings), "llm_enabled", property(lambda self: True))
    monkeypatch.setattr(
        style_search,
        "_complete",
        lambda messages: '{"presentation": "feminine", "length": "long", '
        '"hair_type": null, "maintenance": "high", "face_shape": null}',
    )
    c = style_search.extract_constraints("glamorous going-out hair")
    assert c.source == "llm"
    assert c.presentation is Presentation.feminine
    assert c.length is Length.long
    assert c.maintenance is Maintenance.high


def test_llm_values_outside_the_vocabulary_are_dropped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = get_settings()
    monkeypatch.setattr(type(settings), "llm_enabled", property(lambda self: True))
    monkeypatch.setattr(
        style_search,
        "_complete",
        lambda messages: '{"length": "extremely short", "maintenance": "low"}',
    )
    c = style_search.extract_constraints("barely any hair at all")
    assert c.length is None
    assert c.maintenance is Maintenance.low


def test_llm_failure_falls_back_to_keywords(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(type(settings), "llm_enabled", property(lambda self: True))

    def boom(messages: list[dict[str, str]]) -> str:
        raise RuntimeError("no network")

    monkeypatch.setattr(style_search, "_complete", boom)
    c = style_search.extract_constraints("curly low maintenance")
    assert c.source == "keywords"
    assert c.hair_type is HairType.curly


def test_empty_llm_extraction_falls_back_to_keywords(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = get_settings()
    monkeypatch.setattr(type(settings), "llm_enabled", property(lambda self: True))
    monkeypatch.setattr(style_search, "_complete", lambda messages: "{}")
    c = style_search.extract_constraints("curly hair please")
    assert c.source == "keywords"
    assert c.hair_type is HairType.curly


# --- ranking ----------------------------------------------------------------


def test_presentation_is_a_hard_filter() -> None:
    _, hits = style_search.search("mens short cut", limit=28)
    for hit in hits:
        assert (
            Presentation.masculine in hit.style.presentations
            or Presentation.unisex in hit.style.presentations
        )


def test_matching_constraints_are_reported_as_reasons() -> None:
    _, hits = style_search.search("low maintenance short cut for curly hair", limit=5)
    assert hits
    assert any(h.reasons for h in hits)


def test_results_are_sorted_by_score() -> None:
    _, hits = style_search.search("long wavy hair", limit=10)
    scores = [h.score for h in hits]
    assert scores == sorted(scores, reverse=True)


def test_limit_is_respected() -> None:
    _, hits = style_search.search("hair", limit=3)
    assert len(hits) <= 3
