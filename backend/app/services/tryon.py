"""Realistic AI try-on: paint the chosen hairstyle into the user's own photo.

Two providers, because they solve the problem differently and cost differently.

**Cloudflare, stable-diffusion-v1-5-inpainting.** The frontend sends a mask
covering the hair region, derived from the face landmarks it already has, and
the model paints hair into that region only. Everything outside the mask is the
original photograph, so identity is preserved by construction rather than by
asking a model nicely. Free on the Workers AI allowance, which is what makes a
public demo affordable.

**fal.ai, Flux Kontext.** Instruction editing over the whole image with a much
stronger model. Better output, but it bills per image and nothing structurally
prevents it from altering the face.

Cloudflare is preferred when a mask is supplied and credentials exist. This is
the honest answer to the flat 2D overlay: that pastes artwork on top of a photo
and always looks pasted. This generates hair inside the photo.
"""

from __future__ import annotations

import base64
import binascii
import json
import logging
import os
import urllib.error
import urllib.request

from app.core.config import get_settings
from app.knowledge.loader import load_styles

logger = logging.getLogger(__name__)


class TryOnError(Exception):
    """Raised when a realistic try-on can't be produced."""


# Provider failures that mean "this will not work until the account is sorted
# out", as opposed to a transient glitch. The raw text from the provider names
# the account's billing state, so it is logged rather than shown to the user.
_ACCOUNT_MARKERS = ("top_up", "locked", "quota", "insufficient", "billing", "payment")


def _user_message(exc: Exception) -> str:
    """A message safe to show an end user, whatever the provider said."""
    detail = str(exc).lower()
    if "allocation" in detail or "neurons" in detail:
        return "Realistic try-on has hit today's free limit. The quick preview still works."
    if any(marker in detail for marker in _ACCOUNT_MARKERS):
        return "Realistic AI try-on is temporarily unavailable. The 2D overlay still works."
    if "rate" in detail and "limit" in detail:
        return "Realistic AI try-on is busy right now. Try again in a moment."
    return "Realistic AI try-on could not generate an image. Try again in a moment."


def _enabled() -> bool:
    return get_settings().ai_tryon_enabled


def _style(style_id: str):  # type: ignore[no-untyped-def]
    styles = {s.id: s for s in load_styles()}
    style = styles.get(style_id)
    if style is None:
        raise TryOnError("Unknown style.")
    return style


def build_prompt(style_id: str) -> str:
    """Instruction prompt for whole-image editing (fal.ai)."""
    style = _style(style_id)
    return (
        f"Change only the hairstyle of the person in this photo to a {style.name}: "
        f"{style.description} Keep the exact same face, identity, skin tone, facial "
        f"hair, expression, pose, lighting and background. Photorealistic, natural "
        f"hair that blends realistically with the head."
    )


def build_inpaint_prompt(style_id: str) -> str:
    """Descriptive prompt for inpainting.

    Inpainting fills a region, so this describes what should be there rather
    than instructing a change. Naming the photographic qualities matters: the
    painted region has to sit inside a real photograph without looking drawn.
    """
    style = _style(style_id)
    return (
        f"photograph of a person with a {style.name} hairstyle, {style.description} "
        "Realistic human hair with individual strands and natural texture, "
        "soft natural hairline, lighting and colour matching the rest of the photo, "
        "sharp focus, photorealistic."
    )


INPAINT_NEGATIVE = (
    "cartoon, drawing, illustration, painting, wig, helmet, hat, blurry, smeared, "
    "deformed, distorted face, second face, extra head, text, watermark, low quality"
)


def _decode_data_url(data_url: str, what: str) -> bytes:
    """Bytes from a data URL, raising a clean error if it is malformed."""
    marker = "base64,"
    idx = data_url.find(marker)
    payload = data_url[idx + len(marker) :] if idx != -1 else data_url
    try:
        raw = base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise TryOnError(f"The {what} could not be read.") from exc
    if not raw:
        raise TryOnError(f"The {what} was empty.")
    return raw


def _run_fal(model: str, prompt: str, image_url: str) -> dict:
    """Isolated network call (monkeypatched in tests)."""
    import fal_client

    return fal_client.run(
        model,
        arguments={"prompt": prompt, "image_url": image_url},
    )


def _run_cloudflare_inpaint(
    account_id: str,
    token: str,
    model: str,
    prompt: str,
    image_bytes: bytes,
    mask_bytes: bytes,
) -> bytes:
    """Isolated network call (monkeypatched in tests). Returns PNG bytes."""
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}"
    body = {
        "prompt": prompt,
        "negative_prompt": INPAINT_NEGATIVE,
        "image_b64": base64.b64encode(image_bytes).decode(),
        # Cloudflare documents the mask as an array of 8-bit unsigned integers.
        "mask": list(mask_bytes),
        "num_steps": 20,
        "strength": 1,
        "guidance": 7.5,
    }
    req = urllib.request.Request(url, method="POST")
    req.add_header("Authorization", "Bearer " + token)
    req.add_header("Content-Type", "application/json")
    req.data = json.dumps(body).encode()

    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            payload, ctype = resp.read(), resp.headers.get("Content-Type", "")
    except urllib.error.HTTPError as exc:
        detail = exc.read()[:400].decode(errors="ignore")
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc

    if ctype.startswith("image/"):
        return payload

    data = json.loads(payload)
    if not data.get("success", True):
        raise RuntimeError(json.dumps(data.get("errors"))[:400])
    encoded = data.get("result", {}).get("image")
    if not encoded:
        raise RuntimeError("inpainting returned no image")
    return base64.b64decode(encoded)


def generate_tryon(
    image_data_url: str,
    style_id: str,
    mask_data_url: str | None = None,
) -> str:
    """A photorealistic image of the user wearing the style.

    Returns a data URL when inpainting locally-generated bytes, or the
    provider's URL when fal.ai produced it. Both work as an image source.
    """
    settings = get_settings()
    if not _enabled():
        raise TryOnError("Realistic AI try-on is not configured.")

    # Inpainting needs a mask. With one, it is both free and structurally
    # safer, because the face is never inside the edited region.
    if mask_data_url and settings.cloudflare_enabled:
        prompt = build_inpaint_prompt(style_id)
        image_bytes = _decode_data_url(image_data_url, "photo")
        mask_bytes = _decode_data_url(mask_data_url, "mask")
        try:
            png = _run_cloudflare_inpaint(
                settings.cloudflare_account_id,
                settings.cloudflare_api_token,
                settings.cloudflare_inpaint_model,
                prompt,
                image_bytes,
                mask_bytes,
            )
        except TryOnError:
            raise
        except Exception as exc:
            logger.warning("cloudflare inpaint failed for style %s: %s", style_id, exc)
            raise TryOnError(_user_message(exc)) from exc
        return "data:image/png;base64," + base64.b64encode(png).decode()

    if not settings.fal_key.strip():
        raise TryOnError("Realistic AI try-on is not configured.")

    os.environ["FAL_KEY"] = settings.fal_key
    prompt = build_prompt(style_id)
    try:
        result = _run_fal(settings.fal_model, prompt, image_data_url)
    except TryOnError:
        raise
    except Exception as exc:  # network / API / quota
        # The provider's own wording can name the account's billing state, so
        # it goes to the log and the user gets something they can act on.
        logger.warning("fal.ai try-on failed for style %s: %s", style_id, exc)
        raise TryOnError(_user_message(exc)) from exc

    images = result.get("images") or []
    if not images or not images[0].get("url"):
        raise TryOnError("The AI try-on returned no image.")
    return str(images[0]["url"])
