"""Schemas for the realistic AI try-on endpoint."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TryOnRequest(BaseModel):
    # The user's front photo as a data URL (data:image/...;base64,...).
    image_data_url: str = Field(..., min_length=32)
    style_id: str


class TryOnResponse(BaseModel):
    image_url: str
