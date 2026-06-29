"""Tests for the Groq LLM explanation layer (mocked — no real API calls)."""

from __future__ import annotations

import pytest
from app.knowledge.loader import load_styles
from app.models.recommend import FaceShape
from app.services import llm
from app.services.explanations import build_rule_based_explanation


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    llm.clear_cache()


def _a_style() -> object:
    return next(s for s in load_styles() if s.id == "blunt-bob")


def test_fallback_when_llm_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(llm, "_llm_enabled", lambda: False)
    style = _a_style()
    result = llm.generate_explanation(style, FaceShape.oval)
    assert result.source == "fallback"
    assert result.cached is False
    assert result.text == build_rule_based_explanation(style, FaceShape.oval)


def test_uses_llm_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(llm, "_llm_enabled", lambda: True)
    monkeypatch.setattr(llm, "_complete", lambda messages: "A tailored AI explanation.")
    result = llm.generate_explanation(_a_style(), FaceShape.heart)
    assert result.source == "llm"
    assert result.cached is False
    assert result.text == "A tailored AI explanation."


def test_caches_repeated_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    def fake_complete(messages: list[dict[str, str]]) -> str:
        calls["n"] += 1
        return "Cached AI explanation."

    monkeypatch.setattr(llm, "_llm_enabled", lambda: True)
    monkeypatch.setattr(llm, "_complete", fake_complete)
    style = _a_style()

    first = llm.generate_explanation(style, FaceShape.diamond)
    second = llm.generate_explanation(style, FaceShape.diamond)

    assert calls["n"] == 1  # second call served from cache
    assert first.cached is False
    assert second.cached is True
    assert second.source == "llm"


def test_falls_back_on_api_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(messages: list[dict[str, str]]) -> str:
        raise RuntimeError("rate limited")

    monkeypatch.setattr(llm, "_llm_enabled", lambda: True)
    monkeypatch.setattr(llm, "_complete", boom)
    style = _a_style()
    result = llm.generate_explanation(style, FaceShape.square)
    assert result.source == "fallback"
    assert result.text == build_rule_based_explanation(style, FaceShape.square)


def test_falls_back_on_empty_completion(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(llm, "_llm_enabled", lambda: True)
    monkeypatch.setattr(llm, "_complete", lambda messages: "   ")
    result = llm.generate_explanation(_a_style(), FaceShape.round)
    assert result.source == "fallback"
