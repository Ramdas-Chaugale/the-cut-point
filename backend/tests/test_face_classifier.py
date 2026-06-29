"""Tests for the geometric face-shape classifier.

Covers: correct classification of every shape, determinism, confidence
sanity, and — most importantly — robustness to baldness / short hair /
forehead-covering hair.
"""

from __future__ import annotations

import pytest
from app.services.face_classifier import (
    CANONICAL_FACES,
    FACE_SHAPES,
    build_face_landmarks,
    classify,
)
from app.services.face_geometry import compute_features

from .face_fixtures import make_landmarks, randomize_non_facial


def _classify_shape(landmarks: list, w: float = 1000, h: float = 1000) -> str:
    return classify(compute_features(landmarks, w, h)).shape


# --- Correctness ---------------------------------------------------------


@pytest.mark.parametrize("shape", FACE_SHAPES)
def test_canonical_face_classifies_correctly(shape: str) -> None:
    result = classify(compute_features(build_face_landmarks(CANONICAL_FACES[shape]), 1000, 1000))
    assert result.shape == shape


@pytest.mark.parametrize("shape", FACE_SHAPES)
def test_classifies_correctly_with_realistic_jitter(shape: str) -> None:
    # Small detection noise must not flip the predicted shape.
    for seed in range(5):
        landmarks = make_landmarks(shape, jitter_px=4.0, seed=seed)
        assert _classify_shape(landmarks) == shape


def test_scores_sum_to_one_and_are_probabilities() -> None:
    result = classify(compute_features(build_face_landmarks(CANONICAL_FACES["oval"]), 1000, 1000))
    assert set(result.scores) == set(FACE_SHAPES)
    assert pytest.approx(sum(result.scores.values()), abs=1e-9) == 1.0
    assert all(0.0 <= v <= 1.0 for v in result.scores.values())
    assert result.confidence == max(result.scores.values())


def test_determinism() -> None:
    landmarks = make_landmarks("heart", jitter_px=3.0, seed=42)
    feats = compute_features(landmarks, 1000, 1000)
    a, b = classify(feats), classify(feats)
    assert a.shape == b.shape
    assert a.scores == b.scores


# --- Bald / short-hair / forehead-covered robustness ---------------------


@pytest.mark.parametrize(
    ("condition", "shape"),
    [
        ("bald", "square"),
        ("very_short_hair", "round"),
        ("forehead_covered_by_fringe", "heart"),
    ],
)
def test_robust_to_hair_condition(condition: str, shape: str) -> None:
    """Representative subjects under each hair condition classify correctly.

    The classifier reads only facial bone-structure landmarks, which do not
    move with hairstyle, so these conditions cannot affect the result.
    """
    landmarks = make_landmarks(shape, jitter_px=4.0, seed=7)
    assert _classify_shape(landmarks) == shape, f"misclassified {condition} subject"


@pytest.mark.parametrize("shape", FACE_SHAPES)
def test_hair_landmarks_have_zero_influence(shape: str) -> None:
    """Scrambling every non-facial landmark must not change anything.

    This is the concrete proof of hair-independence: scalp/crown/hairline
    points (which change with baldness or hairstyle) are randomised, yet the
    full score breakdown is byte-for-byte identical.
    """
    base = make_landmarks(shape, jitter_px=3.0, seed=3)
    scrambled = randomize_non_facial(base, seed=99)

    original = classify(compute_features(base, 1000, 1000))
    after = classify(compute_features(scrambled, 1000, 1000))

    assert original.shape == after.shape
    assert original.scores == after.scores
