"""Explainable face-shape classifier.

Approach: prototype matching in a small, interpretable feature space.

1. We define one *canonical* parametric face per shape, straight from facial
   morphology (e.g. a heart face = wide forehead + narrow/pointed jaw; an
   oblong face = much longer than wide with even widths).
2. Each canonical face is run through the **same** geometry code used on real
   input (:func:`app.services.face_geometry.compute_features`), giving a
   prototype feature vector. There are therefore no hand-tuned magic numbers
   that can drift away from the measurement code.
3. A real face is classified by weighted Euclidean distance to each prototype;
   distances become per-shape scores via a softmax, so every result carries a
   calibrated confidence and a full score breakdown.

Because the features are derived only from bone-structure landmarks, the result
is independent of hair — see :mod:`app.services.face_geometry`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from app.services.face_geometry import (
    LM_CHEEK_L,
    LM_CHEEK_R,
    LM_CHIN,
    LM_EYE_OUTER_L,
    LM_EYE_OUTER_R,
    LM_FOREHEAD_L,
    LM_FOREHEAD_R,
    LM_FOREHEAD_TOP,
    LM_JAW_L,
    LM_JAW_R,
    LM_NOSE_TIP,
    FaceFeatures,
    Landmark,
    compute_features,
)

FACE_SHAPES = (
    "oval",
    "round",
    "square",
    "oblong",
    "heart",
    "diamond",
    "triangle",
)

# Vertical placement of each landmark row as a fraction of face length,
# measured from the forehead top (0.0) down to the chin (1.0).
_FOREHEAD_FRAC = 0.10
_CHEEK_FRAC = 0.45
_JAW_FRAC = 0.80
_NOSE_FRAC = 0.55
_EYE_FRAC = 0.35
_TOP_PX = 100.0
_CENTER_X = 500.0
_IMAGE = 1000.0


@dataclass(frozen=True)
class CanonicalFace:
    """Parametric description of an idealised face shape (pixel widths)."""

    face_length: float
    cheek_width: float
    jaw_width: float
    forehead_width: float


# Canonical morphology per shape. cheek_width is the shared reference (300px);
# everything else encodes the defining proportions of that shape.
CANONICAL_FACES: dict[str, CanonicalFace] = {
    # Length ~1.5x width, forehead a touch narrower than cheeks, soft jaw.
    "oval": CanonicalFace(face_length=450, cheek_width=300, jaw_width=234, forehead_width=270),
    # Length ~= width, soft tapering jaw, gently curved.
    "round": CanonicalFace(face_length=315, cheek_width=300, jaw_width=240, forehead_width=276),
    # Length ~= width but forehead/cheek/jaw nearly equal -> strong, square jaw.
    "square": CanonicalFace(face_length=320, cheek_width=300, jaw_width=288, forehead_width=294),
    # Much longer than wide with near-even widths (straight sides).
    "oblong": CanonicalFace(face_length=525, cheek_width=300, jaw_width=276, forehead_width=288),
    # Widest at the forehead, narrow pointed jaw.
    "heart": CanonicalFace(face_length=420, cheek_width=300, jaw_width=198, forehead_width=300),
    # Widest at the cheekbones; both forehead and jaw narrower.
    "diamond": CanonicalFace(face_length=450, cheek_width=300, jaw_width=210, forehead_width=234),
    # Widest at the jaw, narrow forehead (a.k.a. pear).
    "triangle": CanonicalFace(face_length=420, cheek_width=300, jaw_width=312, forehead_width=225),
}

# Feature ordering for distance computation.
# (length_to_width, forehead_to_cheek, jaw_to_cheek, forehead_to_jaw, jaw_angle_deg)
_SCALES = (0.25, 0.12, 0.12, 0.18, 25.0)
_WEIGHTS = (1.0, 1.1, 1.1, 1.0, 0.5)


@dataclass(frozen=True)
class ClassificationResult:
    shape: str
    confidence: float
    scores: dict[str, float]


def build_face_landmarks(face: CanonicalFace, image: float = _IMAGE) -> list[Landmark]:
    """Build a 478-point landmark list for a parametric face.

    Only the bone-structure indices the classifier reads are meaningful; the
    rest are filler. This is the single source of truth for both the prototypes
    and the test fixtures, so fixtures and the model can never silently diverge.
    """
    n = 478
    pts: list[Landmark] = [(0.5, 0.5, 0.0)] * n

    top = _TOP_PX
    fl = face.face_length

    def row_y(frac: float) -> float:
        return (top + frac * fl) / image

    cx = _CENTER_X / image
    chin_y = (top + fl) / image
    top_y = top / image

    def half(width: float) -> float:
        return (width / 2.0) / image

    pts[LM_FOREHEAD_TOP] = (cx, top_y, 0.0)
    pts[LM_CHIN] = (cx, chin_y, 0.0)
    pts[LM_FOREHEAD_R] = (cx - half(face.forehead_width), row_y(_FOREHEAD_FRAC), 0.0)
    pts[LM_FOREHEAD_L] = (cx + half(face.forehead_width), row_y(_FOREHEAD_FRAC), 0.0)
    pts[LM_CHEEK_R] = (cx - half(face.cheek_width), row_y(_CHEEK_FRAC), 0.0)
    pts[LM_CHEEK_L] = (cx + half(face.cheek_width), row_y(_CHEEK_FRAC), 0.0)
    pts[LM_JAW_R] = (cx - half(face.jaw_width), row_y(_JAW_FRAC), 0.0)
    pts[LM_JAW_L] = (cx + half(face.jaw_width), row_y(_JAW_FRAC), 0.0)
    pts[LM_NOSE_TIP] = (cx, row_y(_NOSE_FRAC), 0.0)
    pts[LM_EYE_OUTER_R] = (cx - half(face.cheek_width) * 0.7, row_y(_EYE_FRAC), 0.0)
    pts[LM_EYE_OUTER_L] = (cx + half(face.cheek_width) * 0.7, row_y(_EYE_FRAC), 0.0)
    return pts


def _feature_vector(f: FaceFeatures) -> tuple[float, float, float, float, float]:
    return (
        f.length_to_width,
        f.forehead_to_cheek,
        f.jaw_to_cheek,
        f.forehead_to_jaw,
        f.jaw_angle_deg,
    )


def _build_prototypes() -> dict[str, tuple[float, float, float, float, float]]:
    """Compute prototype feature vectors from the canonical faces."""
    protos: dict[str, tuple[float, float, float, float, float]] = {}
    for shape, face in CANONICAL_FACES.items():
        landmarks = build_face_landmarks(face)
        feats = compute_features(landmarks, _IMAGE, _IMAGE)
        protos[shape] = _feature_vector(feats)
    return protos


PROTOTYPES = _build_prototypes()


def _weighted_sq_distance(
    a: tuple[float, float, float, float, float],
    b: tuple[float, float, float, float, float],
) -> float:
    total = 0.0
    for ai, bi, scale, weight in zip(a, b, _SCALES, _WEIGHTS, strict=True):
        total += weight * ((ai - bi) / scale) ** 2
    return total


def classify(features: FaceFeatures) -> ClassificationResult:
    """Classify a face into one of the seven shapes with a confidence score."""
    fv = _feature_vector(features)
    # Negative half-distance -> softmax gives a smooth, calibrated confidence.
    logits = {shape: -0.5 * _weighted_sq_distance(fv, proto) for shape, proto in PROTOTYPES.items()}
    top = max(logits.values())
    exp = {shape: math.exp(logit - top) for shape, logit in logits.items()}
    denom = sum(exp.values())
    scores = {shape: value / denom for shape, value in exp.items()}
    best = max(scores, key=lambda s: scores[s])
    return ClassificationResult(
        shape=best,
        confidence=scores[best],
        scores=scores,
    )
