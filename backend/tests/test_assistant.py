"""Tests for the catalogue-grounded stylist assistant."""

from __future__ import annotations

import pytest
from app.core.config import get_settings
from app.main import app
from app.models.recommend import FaceShape
from app.services import assistant
from fastapi.testclient import TestClient

client = TestClient(app)


@pytest.fixture(autouse=True)
def _llm_off(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(type(settings), "llm_enabled", property(lambda self: False))


def _enable_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(type(settings), "llm_enabled", property(lambda self: True))


# --- retrieval --------------------------------------------------------------


def test_retrieve_finds_the_style_asked_about() -> None:
    styles = assistant.retrieve("is the wolf cut high maintenance?")
    assert any(s.id == "wolf-cut" for s in styles)


def test_retrieve_always_returns_something() -> None:
    # No catalogue term in the question at all.
    assert assistant.retrieve("hmmm") != []


def test_retrieve_respects_k() -> None:
    assert len(assistant.retrieve("short hair", k=2)) == 2


def test_face_shape_nudges_the_ranking() -> None:
    styles = assistant.retrieve("what suits me", face_shape=FaceShape.round, k=5)
    assert any(FaceShape.round in s.flattering_for for s in styles)


# --- answering --------------------------------------------------------------


def test_answer_falls_back_without_a_key() -> None:
    result = assistant.ask("will a bob work with curly hair?")
    assert result.source == "fallback"
    assert result.text
    assert result.sources


def test_answer_uses_the_llm_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable_llm(monkeypatch)
    monkeypatch.setattr(assistant, "_complete", lambda messages: "Yes, with layers.")
    result = assistant.ask("will a bob work with curly hair?")
    assert result.source == "llm"
    assert result.text == "Yes, with layers."


def test_the_model_only_sees_catalogue_entries(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable_llm(monkeypatch)
    captured: dict[str, str] = {}

    def capture(messages: list[dict[str, str]]) -> str:
        captured["system"] = messages[0]["content"]
        captured["user"] = messages[1]["content"]
        return "Grounded answer."

    monkeypatch.setattr(assistant, "_complete", capture)
    result = assistant.ask("is the wolf cut high maintenance?")

    assert "Catalogue:" in captured["user"]
    assert "only those entries" in captured["system"]
    # Every style named in the prompt is one that came back as a source.
    for style in result.sources:
        assert style.name in captured["user"]


def test_llm_failure_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable_llm(monkeypatch)

    def boom(messages: list[dict[str, str]]) -> str:
        raise RuntimeError("rate limited")

    monkeypatch.setattr(assistant, "_complete", boom)
    result = assistant.ask("what is low maintenance?")
    assert result.source == "fallback"
    assert result.text


def test_empty_completion_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable_llm(monkeypatch)
    monkeypatch.setattr(assistant, "_complete", lambda messages: "   ")
    result = assistant.ask("what is low maintenance?")
    assert result.source == "fallback"


# --- API --------------------------------------------------------------------


def test_assistant_endpoint() -> None:
    resp = client.post("/api/assistant", json={"question": "is a buzz cut low upkeep?"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"]
    assert body["source"] == "fallback"
    assert len(body["sources"]) >= 1
    assert {"id", "name", "description"} <= set(body["sources"][0])


def test_assistant_endpoint_accepts_a_face_shape() -> None:
    resp = client.post(
        "/api/assistant",
        json={"question": "what would suit me?", "face_shape": "square"},
    )
    assert resp.status_code == 200
    assert resp.json()["answer"]


def test_assistant_rejects_an_empty_question() -> None:
    assert client.post("/api/assistant", json={"question": ""}).status_code == 422


def test_search_endpoint_reports_what_it_understood() -> None:
    resp = client.post("/api/search", json={"query": "low maintenance short cut for curly hair"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["parsed"]["maintenance"] == "low"
    assert body["parsed"]["hair_type"] == "curly"
    assert body["parsed"]["source"] == "keywords"
    assert body["count"] == len(body["results"])
    assert body["results"], "expected at least one match"
    front = body["results"][0]["angle_assets"]["front"]
    assert "/front." in front and front.rsplit(".", 1)[1] in {"webp", "svg", "png"}


def test_search_rejects_a_too_short_query() -> None:
    assert client.post("/api/search", json={"query": "a"}).status_code == 422


def test_styles_endpoint_returns_the_whole_catalogue() -> None:
    resp = client.get("/api/styles")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 21
    assert body[0]["try_on_overlay"].endswith("/overlay.svg")
