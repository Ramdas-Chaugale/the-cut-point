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
    # The generated silhouettes (4 angles + try-on overlay) must exist for every
    # style, or the UI would show broken images. Run tools/generate_hair_assets.py.
    for style in load_styles():
        for name in ("front", "left", "right", "back", "overlay"):
            asset = _ASSET_ROOT / style.id / f"{name}.svg"
            assert asset.is_file(), f"Missing asset: {asset}"
