"""CutPoint FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.booking import router as booking_router
from app.api.face import router as face_router
from app.api.recommend import router as recommend_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="CutPoint API",
    description="AI hairstyle recommendation & salon booking backend.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(face_router)
app.include_router(recommend_router)
app.include_router(booking_router)


@app.get("/health", tags=["meta"])
def health() -> dict[str, object]:
    """Liveness probe + basic capability flags for the frontend."""
    return {
        "status": "ok",
        "service": "cutpoint-api",
        "version": app.version,
        "llm_enabled": settings.llm_enabled,
    }
