"""Knowledge-base integrity tests."""

from __future__ import annotations

from pathlib import Path

from app.knowledge.loader import load_styles
from app.models.recommend import RATIONALE_TAGS, FaceShape

_ASSET_ROOT = Path(__file__).resolve().parents[2] / "frontend" / "public" / "assets" / "hair"


def test_kb_loads_and_is_nonempty() -> None:
    styles = load_styles()
    assert len(styles) >= 20


def test_kb_has_unique_ids() -> None:
    ids = [s.id for s in load_styles()]
    assert len(ids) == len(set(ids))


def test_every_face_shape_is_covered() -> None:
    covered = {shape for style in load_styles() for shape in style.flattering_for}
    assert set(FaceShape) <= covered


def test_all_rationale_tags_are_known() -> None:
    for style in load_styles():
        assert set(style.rationale_tags) <= RATIONALE_TAGS


def test_every_style_has_angle_and_overlay_assets() -> None:
    # Every style needs four reference views plus the try-on overlay, or the UI
    # shows broken images. The four angles may be rendered WebP or the older
    # generated SVG, since the catalogue migrates a batch at a time.
    for style in load_styles():
        for name in ("front", "left", "right", "back"):
            found = [
                ext
                for ext in ("webp", "svg", "png")
                if (_ASSET_ROOT / style.id / f"{name}.{ext}").is_file()
            ]
            assert found, f"No asset for {style.id}/{name}.*"

        # The overlay is anchored to face landmarks and scaled, so it has to
        # stay a transparent vector. A render cannot replace it.
        overlay = _ASSET_ROOT / style.id / "overlay.svg"
        assert overlay.is_file(), f"Missing overlay: {overlay}"


def test_resolved_asset_urls_point_at_files_that_exist() -> None:
    # The resolver picks an extension per file, so a mismatch between what it
    # returns and what is on disk would only show up as a 404 in the browser.
    from app.services.assets import ASSET_BASE, angle_assets, overlay_url

    for style in load_styles():
        urls = angle_assets(style.id)
        for angle in ("front", "left", "right", "back"):
            url = getattr(urls, angle)
            assert url.startswith(f"{ASSET_BASE}/{style.id}/")
            assert (_ASSET_ROOT / url[len(ASSET_BASE) + 1 :]).is_file(), url
        overlay = overlay_url(style.id)
        assert (_ASSET_ROOT / overlay[len(ASSET_BASE) + 1 :]).is_file(), overlay
