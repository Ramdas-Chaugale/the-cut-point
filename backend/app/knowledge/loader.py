"""Load and validate the hairstyle knowledge base from YAML."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from app.models.recommend import RATIONALE_TAGS, FaceShape, Style

_KB_PATH = Path(__file__).parent / "hairstyles.yaml"


def _validate(styles: list[Style]) -> None:
    """Sanity-check the curated data beyond per-field type validation."""
    ids = [s.id for s in styles]
    duplicates = {i for i in ids if ids.count(i) > 1}
    if duplicates:
        raise ValueError(f"Duplicate style ids in knowledge base: {sorted(duplicates)}")

    for style in styles:
        unknown = set(style.rationale_tags) - RATIONALE_TAGS
        if unknown:
            raise ValueError(f"Style '{style.id}' has unknown rationale tags: {sorted(unknown)}")
        if not style.flattering_for:
            raise ValueError(f"Style '{style.id}' flatters no face shapes.")

    # Every face shape must have at least one flattering style, or some users
    # would get zero recommendations.
    covered = {shape for style in styles for shape in style.flattering_for}
    missing = set(FaceShape) - covered
    if missing:
        raise ValueError(f"No styles flatter these face shapes: {sorted(s.value for s in missing)}")


@lru_cache
def load_styles() -> tuple[Style, ...]:
    """Return the validated knowledge base (cached for the process lifetime)."""
    raw = yaml.safe_load(_KB_PATH.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or "styles" not in raw:
        raise ValueError("hairstyles.yaml must contain a top-level 'styles' list.")
    styles = [Style.model_validate(item) for item in raw["styles"]]
    _validate(styles)
    return tuple(styles)
