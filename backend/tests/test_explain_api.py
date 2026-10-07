"""Tests for the /api/explain endpoint."""

from __future__ import annotations

import pytest
from app.main import app
from app.services import llm
from fastapi.testclient import TestClient

client = TestClient(app)


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    llm.clear_cache()


def test_explain_returns_fallback_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(llm, "_llm_enabled", lambda: False)
    resp = client.post(
        "/api/explain",
        json={"style_id": "blunt-bob", "face_shape": "oval"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["style_id"] == "blunt-bob"
    assert body["source"] == "fallback"
    assert len(body["explanation"]) > 0


def test_explain_uses_llm_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(llm, "_llm_enabled", lambda: True)
    monkeypatch.setattr(llm, "_complete", lambda messages: "Bespoke AI text.")
    resp = client.post(
        "/api/explain",
        json={"style_id": "textured-pixie", "face_shape": "heart", "hair_type": "wavy"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["source"] == "llm"
    assert body["explanation"] == "Bespoke AI text."


def test_explain_unknown_style_404() -> None:
    resp = client.post(
        "/api/explain",
        json={"style_id": "does-not-exist", "face_shape": "oval"},
    )
    assert resp.status_code == 404
