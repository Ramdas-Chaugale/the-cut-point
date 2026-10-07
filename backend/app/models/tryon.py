"""Schemas for the realistic AI try-on endpoint."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TryOnRequest(BaseModel):
    # The user's front photo as a data URL (data:image/...;base64,...).
    image_data_url: str = Field(..., min_length=32)
    style_id: str
    # Optional hair-region mask, white where hair should be painted. The
    # frontend builds it from the face landmarks it already holds. When it is
    # present the free inpainting provider is used, which cannot touch the face
    # because the face is outside the mask.
    mask_data_url: str | None = None


class TryOnResponse(BaseModel):
    image_url: str
