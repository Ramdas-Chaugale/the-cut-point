"""Face-analysis API router."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.models.face import (
    SHAPE_DESCRIPTIONS,
    AnalyzeRequest,
    AnalyzeResponse,
    Orientation,
    Quality,
)
from app.services.face_classifier import classify
from app.services.face_geometry import compute_features

router = APIRouter(prefix="/api/face", tags=["face"])

# Below this, the face occupies too little of the frame for reliable ratios.
_MIN_FACE_SIZE_RATIO = 0.15


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_face(payload: AnalyzeRequest) -> AnalyzeResponse:
    """Classify face shape from MediaPipe landmarks (geometry-based).

    The browser is responsible for handling no-face / multiple-faces before
    calling this endpoint; here we add quality + orientation warnings so the
    user knows when a result may be less reliable.
    """
    landmarks = [(p[0], p[1], p[2]) for p in payload.landmarks]
    try:
        features = compute_features(landmarks, payload.image_width, payload.image_height)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    result = classify(features)

    warnings: list[str] = []
    if not features.is_frontal:
        warnings.append(
            "The face looks turned to one side. For the most accurate result, "
            "use a straight, front-facing photo."
        )
    if features.face_size_ratio < _MIN_FACE_SIZE_RATIO:
        warnings.append(
            "The face is small in the frame. Move closer or crop in for a more "
            "reliable measurement."
        )

    return AnalyzeResponse(
        shape=result.shape,
        confidence=round(result.confidence, 4),
        description=SHAPE_DESCRIPTIONS[result.shape],
        scores={k: round(v, 4) for k, v in result.scores.items()},
        ratios=features.as_dict(),
        orientation=Orientation(
            yaw_ratio=round(features.yaw_ratio, 4),
            is_frontal=features.is_frontal,
        ),
        quality=Quality(
            face_size_ratio=round(features.face_size_ratio, 4),
            warnings=warnings,
        ),
    )
