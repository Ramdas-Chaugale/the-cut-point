"""Geometric feature extraction from MediaPipe FaceMesh landmarks.

The classifier consumes *only* facial bone-structure landmarks (jaw, cheekbone,
forehead, chin). None of these are hair landmarks, which is exactly why the
face-shape result is independent of hairstyle / baldness / a covered forehead.

MediaPipe returns landmarks normalised to [0, 1] relative to the source image.
Because images are rarely square, a normalised horizontal delta of 0.1 is *not*
the same number of pixels as a vertical delta of 0.1. We therefore convert to
pixel space (x * width, y * height) before measuring any distance or angle.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# --- Canonical MediaPipe FaceMesh landmark indices (468-point model) ---
# Bone-structure points used for classification:
LM_CHIN = 152  # lowest point of the chin
LM_FOREHEAD_TOP = 10  # top-centre of the forehead (face-oval apex)
LM_CHEEK_R = 234  # right cheekbone extreme (subject's right / image left)
LM_CHEEK_L = 454  # left cheekbone extreme
LM_JAW_R = 172  # right jaw / gonial corner
LM_JAW_L = 397  # left jaw / gonial corner
LM_FOREHEAD_R = 54  # right temple / forehead corner
LM_FOREHEAD_L = 284  # left temple / forehead corner

# Points used only for head-orientation (frontal-ness) estimation:
LM_NOSE_TIP = 1
LM_EYE_OUTER_R = 33
LM_EYE_OUTER_L = 263

# Every index this module reads. Used to validate input and to document that
# no hair landmarks are involved.
REQUIRED_INDICES = (
    LM_CHIN,
    LM_FOREHEAD_TOP,
    LM_CHEEK_R,
    LM_CHEEK_L,
    LM_JAW_R,
    LM_JAW_L,
    LM_FOREHEAD_R,
    LM_FOREHEAD_L,
    LM_NOSE_TIP,
    LM_EYE_OUTER_R,
    LM_EYE_OUTER_L,
)

Landmark = tuple[float, float, float]


@dataclass(frozen=True)
class FaceFeatures:
    """Dimensionless ratios + supporting measurements for one face.

    All ratios are normalised against cheekbone (bizygomatic) width, the most
    stable horizontal reference, so they are scale- and distance-invariant.
    """

    # Raw pixel measurements (useful for transparency / debugging).
    face_length_px: float
    cheekbone_width_px: float
    jaw_width_px: float
    forehead_width_px: float

    # Core dimensionless features fed to the classifier.
    length_to_width: float  # face_length / cheekbone_width
    forehead_to_cheek: float  # forehead_width / cheekbone_width
    jaw_to_cheek: float  # jaw_width / cheekbone_width
    forehead_to_jaw: float  # forehead_width / jaw_width
    jaw_angle_deg: float  # jawline angularity (lower = sharper/squarer)

    # Head orientation (for "not front-facing" detection).
    yaw_ratio: float  # signed nose offset / cheek width; ~0 when frontal
    is_frontal: bool

    # Relative face size in frame (for "too far / too small" detection).
    face_size_ratio: float  # cheekbone_width / image_width

    def as_dict(self) -> dict[str, float]:
        """Round-tripped, UI-friendly view of the dimensionless features."""
        return {
            "length_to_width": round(self.length_to_width, 4),
            "forehead_to_cheek": round(self.forehead_to_cheek, 4),
            "jaw_to_cheek": round(self.jaw_to_cheek, 4),
            "forehead_to_jaw": round(self.forehead_to_jaw, 4),
            "jaw_angle_deg": round(self.jaw_angle_deg, 2),
        }


def _px(landmarks: list[Landmark], index: int, w: float, h: float) -> tuple[float, float]:
    """Return landmark ``index`` in pixel coordinates."""
    x, y, _z = landmarks[index]
    return (x * w, y * h)


def _dist(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _angle_at(
    vertex: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
) -> float:
    """Interior angle (degrees) at ``vertex`` formed by p1-vertex-p2."""
    v1 = (p1[0] - vertex[0], p1[1] - vertex[1])
    v2 = (p2[0] - vertex[0], p2[1] - vertex[1])
    n1 = math.hypot(*v1)
    n2 = math.hypot(*v2)
    if n1 == 0 or n2 == 0:
        return 180.0
    cos = (v1[0] * v2[0] + v1[1] * v2[1]) / (n1 * n2)
    cos = max(-1.0, min(1.0, cos))
    return math.degrees(math.acos(cos))


def validate_landmarks(landmarks: list[Landmark]) -> None:
    """Raise ValueError if the landmark list can't be used for analysis."""
    if len(landmarks) <= max(REQUIRED_INDICES):
        raise ValueError(
            f"Expected at least {max(REQUIRED_INDICES) + 1} landmarks, " f"got {len(landmarks)}."
        )


def compute_features(
    landmarks: list[Landmark],
    image_width: float,
    image_height: float,
) -> FaceFeatures:
    """Compute geometric face-shape features from FaceMesh landmarks."""
    validate_landmarks(landmarks)
    w, h = float(image_width), float(image_height)

    chin = _px(landmarks, LM_CHIN, w, h)
    forehead_top = _px(landmarks, LM_FOREHEAD_TOP, w, h)
    cheek_r = _px(landmarks, LM_CHEEK_R, w, h)
    cheek_l = _px(landmarks, LM_CHEEK_L, w, h)
    jaw_r = _px(landmarks, LM_JAW_R, w, h)
    jaw_l = _px(landmarks, LM_JAW_L, w, h)
    fore_r = _px(landmarks, LM_FOREHEAD_R, w, h)
    fore_l = _px(landmarks, LM_FOREHEAD_L, w, h)
    nose = _px(landmarks, LM_NOSE_TIP, w, h)

    face_length = _dist(chin, forehead_top)
    cheek_width = _dist(cheek_r, cheek_l)
    jaw_width = _dist(jaw_r, jaw_l)
    forehead_width = _dist(fore_r, fore_l)

    if cheek_width == 0:
        raise ValueError("Degenerate landmarks: zero cheekbone width.")

    # Jaw angularity: angle of the jawline at each gonial corner
    # (cheek -> jaw corner -> chin). Sharper corners (square jaw) give a
    # smaller angle; softly curved jaws (round/oval) give a larger one.
    angle_r = _angle_at(jaw_r, cheek_r, chin)
    angle_l = _angle_at(jaw_l, cheek_l, chin)
    jaw_angle = (angle_r + angle_l) / 2.0

    # Orientation: signed horizontal offset of the nose from the cheek
    # midline, normalised by cheek width. ~0 when looking straight ahead.
    cheek_mid_x = (cheek_r[0] + cheek_l[0]) / 2.0
    yaw_ratio = (nose[0] - cheek_mid_x) / cheek_width
    is_frontal = abs(yaw_ratio) <= 0.12

    return FaceFeatures(
        face_length_px=face_length,
        cheekbone_width_px=cheek_width,
        jaw_width_px=jaw_width,
        forehead_width_px=forehead_width,
        length_to_width=face_length / cheek_width,
        forehead_to_cheek=forehead_width / cheek_width,
        jaw_to_cheek=jaw_width / cheek_width,
        forehead_to_jaw=forehead_width / jaw_width if jaw_width else 1.0,
        jaw_angle_deg=jaw_angle,
        yaw_ratio=yaw_ratio,
        is_frontal=is_frontal,
        face_size_ratio=cheek_width / w if w else 0.0,
    )
