"""Pydantic schemas for the face-analysis API."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

# Human-readable descriptions shown to the user for transparency.
SHAPE_DESCRIPTIONS: dict[str, str] = {
    "oval": "Balanced proportions — length noticeably greater than width, with a "
    "gently rounded jaw. Considered the most versatile shape.",
    "round": "Soft curves with similar length and width and a rounded jaw; "
    "fullest at the cheeks.",
    "square": "Strong, angular jaw with forehead, cheeks and jaw of similar "
    "width; length close to width.",
    "oblong": "Longer than it is wide with fairly straight sides and even "
    "forehead, cheek and jaw widths.",
    "heart": "Widest at the forehead, tapering to a narrow, pointed chin.",
    "diamond": "Widest at the cheekbones, with a narrower forehead and jaw and a " "pointed chin.",
    "triangle": "Widest at the jaw, narrowing towards the forehead (also called " "a pear shape).",
}


class AnalyzeRequest(BaseModel):
    """Landmarks extracted in-browser by MediaPipe, plus source image size."""

    landmarks: list[list[float]] = Field(
        ...,
        description="MediaPipe FaceMesh landmarks as [x, y, z] in [0,1].",
    )
    image_width: int = Field(..., gt=0)
    image_height: int = Field(..., gt=0)

    @field_validator("landmarks")
    @classmethod
    def _validate_landmarks(cls, value: list[list[float]]) -> list[list[float]]:
        if len(value) < 468:
            raise ValueError(f"Expected at least 468 landmarks, received {len(value)}.")
        for i, point in enumerate(value):
            if len(point) != 3:
                raise ValueError(f"Landmark {i} must have exactly 3 coordinates.")
        return value


class Orientation(BaseModel):
    yaw_ratio: float
    is_frontal: bool


class Quality(BaseModel):
    face_size_ratio: float
    warnings: list[str]


class AnalyzeResponse(BaseModel):
    shape: str
    confidence: float
    description: str
    scores: dict[str, float]
    ratios: dict[str, float]
    orientation: Orientation
    quality: Quality
