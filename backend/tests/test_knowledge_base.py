"""Knowledge-base integrity tests."""

from __future__ import annotations

from app.knowledge.loader import load_styles
from app.models.recommend import RATIONALE_TAGS, FaceShape


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
