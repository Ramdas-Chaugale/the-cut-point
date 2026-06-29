"""Reusable landmark fixtures for face-shape tests.

Fixtures are built from the same canonical parametric model the classifier uses
(:func:`app.services.face_classifier.build_face_landmarks`), so they exercise the
real geometry + classification code rather than a parallel re-implementation.
Small Gaussian jitter simulates real-world landmark noise.
"""

from __future__ import annotations

import random

from app.services.face_classifier import CANONICAL_FACES, build_face_landmarks
from app.services.face_geometry import REQUIRED_INDICES, Landmark

_FACIAL = set(REQUIRED_INDICES)


def make_landmarks(shape: str, *, jitter_px: float = 0.0, seed: int = 0) -> list[Landmark]:
    """Landmarks for a canonical shape, optionally with realistic jitter.

    Jitter is applied only to the facial bone-structure points (the ones the
    classifier actually reads), modelling normal landmark-detection noise.
    """
    pts = build_face_landmarks(CANONICAL_FACES[shape])
    if jitter_px <= 0:
        return pts
    rng = random.Random(seed)
    out = list(pts)
    for idx in _FACIAL:
        x, y, z = out[idx]
        out[idx] = (
            x + rng.gauss(0, jitter_px) / 1000.0,
            y + rng.gauss(0, jitter_px) / 1000.0,
            z,
        )
    return out


def randomize_non_facial(landmarks: list[Landmark], *, seed: int = 1) -> list[Landmark]:
    """Replace every NON-facial landmark with random noise.

    Used to prove the classifier is hair-independent: scalp / crown / hairline
    points (which shift with hairstyle or baldness) are scrambled, and the
    result must not change.
    """
    rng = random.Random(seed)
    out = list(landmarks)
    for idx in range(len(out)):
        if idx in _FACIAL:
            continue
        out[idx] = (rng.random(), rng.random(), rng.uniform(-0.1, 0.1))
    return out
