"""Rule-based 'why it suits you' explanations.

This is the deterministic fallback that always works with no LLM key. Phase 4
wraps it with a Groq-generated, more natural explanation, degrading to this
text whenever the LLM is unavailable.
"""

from __future__ import annotations

from app.models.recommend import FaceShape, Style

# How each rationale tag reads in a sentence.
_TAG_PHRASES: dict[str, str] = {
    "adds-height": "adds height to lengthen the face",
    "elongates": "creates a longer, slimmer line",
    "softens-angles": "softens strong angles",
    "adds-width": "adds width to balance a longer face",
    "balances-forehead": "balances a wider forehead",
    "balances-jaw": "draws the eye up from the jaw",
    "frames-face": "frames the face nicely",
    "highlights-bone-structure": "shows off your bone structure",
    "adds-texture": "adds flattering texture",
    "adds-volume": "builds volume where it helps",
    "low-upkeep": "is easy to maintain",
    "shortens-face": "visually shortens a longer face",
}

_SHAPE_GOAL: dict[FaceShape, str] = {
    FaceShape.oval: "keeps your already-balanced proportions",
    FaceShape.round: "adds length and structure to a rounder face",
    FaceShape.square: "softens a strong, angular jaw",
    FaceShape.oblong: "adds width and shortens a longer face",
    FaceShape.heart: "balances a wider forehead with a narrower chin",
    FaceShape.diamond: "softens prominent cheekbones",
    FaceShape.triangle: "adds volume up top to balance a wider jaw",
}


def _join(parts: list[str]) -> str:
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + " and " + parts[-1]


def build_rule_based_explanation(style: Style, face_shape: FaceShape) -> str:
    """Compose a deterministic explanation from the style's rationale tags."""
    phrases = [_TAG_PHRASES[t] for t in style.rationale_tags if t in _TAG_PHRASES]
    effects = _join(phrases)
    goal = _SHAPE_GOAL[face_shape]
    if effects:
        return (
            f"The {style.name} {goal}: it {effects}. "
            f"A solid match for a {face_shape.value} face shape."
        )
    return f"The {style.name} {goal} — a good fit for a {face_shape.value} face shape."
