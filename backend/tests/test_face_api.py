"""Tests for the /api/face/analyze endpoint."""

from __future__ import annotations

from app.main import app
from app.services.face_classifier import CANONICAL_FACES, build_face_landmarks
from fastapi.testclient import TestClient

from .face_fixtures import make_landmarks

client = TestClient(app)


def _payload(shape: str, w: int = 1000, h: int = 1000) -> dict:
    landmarks = build_face_landmarks(CANONICAL_FACES[shape])
    return {
        "landmarks": [list(p) for p in landmarks],
        "image_width": w,
        "image_height": h,
    }


def test_analyze_returns_expected_shape() -> None:
    resp = client.post("/api/face/analyze", json=_payload("heart"))
    assert resp.status_code == 200
    body = resp.json()
    assert body["shape"] == "heart"
    assert 0.0 <= body["confidence"] <= 1.0
    assert set(body["scores"]) == set(CANONICAL_FACES)
    assert "length_to_width" in body["ratios"]
    assert body["orientation"]["is_frontal"] is True
    assert body["quality"]["warnings"] == []


def test_analyze_rejects_too_few_landmarks() -> None:
    resp = client.post(
        "/api/face/analyze",
        json={"landmarks": [[0.5, 0.5, 0.0]] * 10, "image_width": 100, "image_height": 100},
    )
    assert resp.status_code == 422


def test_analyze_warns_when_not_frontal() -> None:
    # Shift the nose far to one side to simulate a turned head.
    landmarks = [list(p) for p in make_landmarks("oval")]
    from app.services.face_geometry import LM_NOSE_TIP

    landmarks[LM_NOSE_TIP][0] = 0.62  # push nose off the cheek midline
    resp = client.post(
        "/api/face/analyze",
        json={"landmarks": landmarks, "image_width": 1000, "image_height": 1000},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["orientation"]["is_frontal"] is False
    assert any("front-facing" in w for w in body["quality"]["warnings"])
