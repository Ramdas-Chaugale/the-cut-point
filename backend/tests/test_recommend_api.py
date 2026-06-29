"""Tests for the /api/recommend endpoint."""

from __future__ import annotations

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_recommend_endpoint_returns_ranked_styles() -> None:
    resp = client.post(
        "/api/recommend",
        json={
            "face_shape": "heart",
            "presentation": "feminine",
            "desired_length": "medium",
            "hair_type": "wavy",
            "maintenance": "low",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["face_shape"] == "heart"
    assert body["count"] == len(body["recommendations"])
    assert body["count"] >= 1
    first = body["recommendations"][0]
    assert {"id", "name", "match_score", "matched_on", "explanation"} <= set(first)
    scores = [r["match_score"] for r in body["recommendations"]]
    assert scores == sorted(scores, reverse=True)


def test_recommend_minimal_request() -> None:
    resp = client.post("/api/recommend", json={"face_shape": "oval"})
    assert resp.status_code == 200
    assert resp.json()["count"] >= 1


def test_recommend_rejects_unknown_face_shape() -> None:
    resp = client.post("/api/recommend", json={"face_shape": "potato"})
    assert resp.status_code == 422
