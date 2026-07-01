"""Realistic AI try-on tests (fal.ai fully mocked — no real API calls)."""

from __future__ import annotations

import pytest
from app.main import app
from app.services import tryon
from fastapi.testclient import TestClient

client = TestClient(app)

_IMG = "data:image/jpeg;base64," + "A" * 64


def test_build_prompt_known_style() -> None:
    prompt = tryon.build_prompt("pompadour")
    assert "Pompadour" in prompt
    assert "same face" in prompt.lower() or "identity" in prompt.lower()


def test_build_prompt_unknown_style() -> None:
    with pytest.raises(tryon.TryOnError):
        tryon.build_prompt("does-not-exist")


def test_generate_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tryon, "_enabled", lambda: False)
    with pytest.raises(tryon.TryOnError):
        tryon.generate_tryon(_IMG, "pompadour")


def test_generate_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tryon, "_enabled", lambda: True)
    monkeypatch.setattr(
        tryon,
        "_run_fal",
        lambda model, prompt, image_url: {"images": [{"url": "https://cdn.fal/out.png"}]},
    )
    assert tryon.generate_tryon(_IMG, "pompadour") == "https://cdn.fal/out.png"


def test_generate_upstream_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(model: str, prompt: str, image_url: str) -> dict:
        raise RuntimeError("quota exceeded")

    monkeypatch.setattr(tryon, "_enabled", lambda: True)
    monkeypatch.setattr(tryon, "_run_fal", boom)
    with pytest.raises(tryon.TryOnError):
        tryon.generate_tryon(_IMG, "pompadour")


def test_endpoint_unavailable_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tryon, "_enabled", lambda: False)
    resp = client.post(
        "/api/tryon/generate", json={"image_data_url": _IMG, "style_id": "pompadour"}
    )
    assert resp.status_code == 503


def test_endpoint_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tryon, "_enabled", lambda: True)
    monkeypatch.setattr(
        tryon,
        "_run_fal",
        lambda model, prompt, image_url: {"images": [{"url": "https://cdn.fal/out.png"}]},
    )
    resp = client.post(
        "/api/tryon/generate", json={"image_data_url": _IMG, "style_id": "pompadour"}
    )
    assert resp.status_code == 200
    assert resp.json()["image_url"] == "https://cdn.fal/out.png"
