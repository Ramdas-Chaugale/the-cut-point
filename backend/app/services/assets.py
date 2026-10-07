"""Where the frontend should look for each style's pictures.

The four angle views were hand-drawn SVGs and are being replaced by rendered
WebP. Rather than hardcode an extension in two routers and have them drift, or
flip everything the moment the first render lands, this resolves each URL from
what is actually on disk, preferring WebP and falling back to the SVG.

That makes a partly-migrated catalogue render correctly instead of showing
broken images, which matters while the renders are produced a batch at a time
against a daily free allowance.

The scan runs once and is cached for the process lifetime. Adding renders
therefore needs a restart, which is what happens on deploy anyway.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from app.models.recommend import AngleAssets

# Served by Next.js from frontend/public.
ASSET_BASE = "/assets/hair"

# Where those files actually live, so the extension can be checked.
_ASSET_ROOT = Path(__file__).resolve().parents[3] / "frontend" / "public" / "assets" / "hair"

ANGLES = ("front", "left", "right", "back")

# Best first. WebP is a fraction of the size at the sizes the UI displays.
_PREFERRED = ("webp", "svg", "png")


@lru_cache
def _extension(style_id: str, angle: str) -> str:
    """The extension present on disk for one angle, preferring WebP."""
    for ext in _PREFERRED:
        if (_ASSET_ROOT / style_id / f"{angle}.{ext}").is_file():
            return ext
    # Nothing on disk. Point at the SVG so the 404 names the file that is
    # missing rather than something that was never going to exist.
    return "svg"


def angle_assets(style_id: str) -> AngleAssets:
    """URLs for the four reference views of a style."""
    base = f"{ASSET_BASE}/{style_id}"
    return AngleAssets(**{a: f"{base}/{a}.{_extension(style_id, a)}" for a in ANGLES})


def overlay_url(style_id: str) -> str:
    """The transparent front-hair shape used by the 2D try-on.

    Always the SVG. The try-on anchors this to the user's face landmarks and
    scales it, so it has to stay a vector with a transparent background. A
    rendered photograph cannot do that job, which is why the renders replace
    the four reference views and not this.
    """
    return f"{ASSET_BASE}/{style_id}/overlay.svg"


def clear_cache() -> None:
    """Forget the resolved extensions (used in tests, and after new renders)."""
    _extension.cache_clear()
