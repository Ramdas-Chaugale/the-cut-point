"""Realistic AI try-on via fal.ai (Flux Kontext instruction image-editing).

Takes the user's real photo and a target style from our catalog, and asks the
model to change *only* the hairstyle while keeping the person's identity. This
is the genuine neural-hair feature (distinct from the fast 2D overlay). It's
gated on FAL_KEY: with no key configured, the endpoint reports it's unavailable
and the frontend simply hides it.
"""

from __future__ import annotations

import os

from app.core.config import get_settings
from app.knowledge.loader import load_styles


class TryOnError(Exception):
    """Raised when a realistic try-on can't be produced."""


def _enabled() -> bool:
    return get_settings().ai_tryon_enabled


def build_prompt(style_id: str) -> str:
    styles = {s.id: s for s in load_styles()}
    style = styles.get(style_id)
    if style is None:
        raise TryOnError("Unknown style.")
    return (
        f"Change only the hairstyle of the person in this photo to a {style.name}: "
        f"{style.description} Keep the exact same face, identity, skin tone, facial "
        f"hair, expression, pose, lighting and background. Photorealistic, natural "
        f"hair that blends realistically with the head."
    )


def _run_fal(model: str, prompt: str, image_url: str) -> dict:
    """Isolated network call (monkeypatched in tests)."""
    import fal_client

    return fal_client.run(
        model,
        arguments={"prompt": prompt, "image_url": image_url},
    )


def generate_tryon(image_data_url: str, style_id: str) -> str:
    """Return the URL of a photorealistic image of the user wearing the style."""
    settings = get_settings()
    if not _enabled():
        raise TryOnError("Realistic AI try-on is not configured.")

    os.environ["FAL_KEY"] = settings.fal_key
    prompt = build_prompt(style_id)
    try:
        result = _run_fal(settings.fal_model, prompt, image_data_url)
    except TryOnError:
        raise
    except Exception as exc:  # network / API / quota
        raise TryOnError(f"The AI try-on service failed: {exc}") from exc

    images = result.get("images") or []
    if not images or not images[0].get("url"):
        raise TryOnError("The AI try-on returned no image.")
    return str(images[0]["url"])
