"""LLM explanation layer (Groq) with caching and graceful fallback.

Design goals:
- Never break the demo: if no GROQ_API_KEY is set, or the API call fails for
  any reason, we fall back to the deterministic rule-based explanation.
- Cheap and fast: results are cached in-memory per (style, face shape,
  preferences) so repeated requests don't re-call the API.
- Testable: the network call is isolated in ``_complete`` and the enabled
  check in ``_llm_enabled`` so both can be monkeypatched.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import get_settings
from app.models.recommend import (
    FaceShape,
    HairType,
    Length,
    Maintenance,
    Presentation,
    Style,
)
from app.services.explanations import build_rule_based_explanation

_SYSTEM_PROMPT = (
    "You are a friendly, professional hairstylist. In no more than two short "
    "sentences, explain why a specific hairstyle suits a client's face shape. "
    "Be specific and factual, reference the face shape by name, and avoid hype, "
    "lists and markdown. Do not restate the question or begin with filler like "
    '"Sure" or "Certainly".'
)

# Cache key -> generated text. Process-lifetime, in-memory (fine for a single
# instance; a production deployment would use a shared cache).
_cache: dict[tuple[str, ...], str] = {}


@dataclass(frozen=True)
class ExplanationResult:
    text: str
    source: str  # "llm" | "fallback"
    cached: bool


def _llm_enabled() -> bool:
    return get_settings().llm_enabled


def _cache_key(
    style: Style,
    face_shape: FaceShape,
    presentation: Presentation | None,
    desired_length: Length | None,
    hair_type: HairType | None,
    maintenance: Maintenance | None,
) -> tuple[str, ...]:
    return (
        style.id,
        face_shape.value,
        presentation.value if presentation else "-",
        desired_length.value if desired_length else "-",
        hair_type.value if hair_type else "-",
        maintenance.value if maintenance else "-",
    )


def _build_messages(
    style: Style,
    face_shape: FaceShape,
    presentation: Presentation | None,
    desired_length: Length | None,
    hair_type: HairType | None,
    maintenance: Maintenance | None,
) -> list[dict[str, str]]:
    prefs: list[str] = []
    if presentation:
        prefs.append(f"presentation: {presentation.value}")
    if desired_length:
        prefs.append(f"preferred length: {desired_length.value}")
    if hair_type:
        prefs.append(f"hair type: {hair_type.value}")
    if maintenance:
        prefs.append(f"maintenance preference: {maintenance.value}")
    prefs_line = f"\nClient preferences — {', '.join(prefs)}." if prefs else ""

    user = (
        f"Face shape: {face_shape.value}.\n"
        f"Hairstyle: {style.name} — {style.description}\n"
        f"Length: {style.length.value}; maintenance: {style.maintenance.value}.\n"
        f"Why it flatters {face_shape.value} faces (effects): "
        f"{', '.join(style.rationale_tags)}."
        f"{prefs_line}\n"
        "Write the two-sentence explanation."
    )
    return [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


def _complete(messages: list[dict[str, str]]) -> str:
    """Call Groq and return the completion text. Isolated for testing."""
    from groq import Groq  # imported lazily so a missing key never blocks import

    settings = get_settings()
    client = Groq(api_key=settings.groq_api_key)
    completion = client.chat.completions.create(
        model=settings.groq_model,
        messages=messages,  # type: ignore[arg-type]
        temperature=0.5,
        max_tokens=400,
    )
    return (completion.choices[0].message.content or "").strip()


def generate_explanation(
    style: Style,
    face_shape: FaceShape,
    *,
    presentation: Presentation | None = None,
    desired_length: Length | None = None,
    hair_type: HairType | None = None,
    maintenance: Maintenance | None = None,
) -> ExplanationResult:
    """Return an LLM explanation, falling back to rule-based text on any issue."""
    fallback = build_rule_based_explanation(style, face_shape)

    if not _llm_enabled():
        return ExplanationResult(text=fallback, source="fallback", cached=False)

    key = _cache_key(style, face_shape, presentation, desired_length, hair_type, maintenance)
    if key in _cache:
        return ExplanationResult(text=_cache[key], source="llm", cached=True)

    try:
        messages = _build_messages(
            style, face_shape, presentation, desired_length, hair_type, maintenance
        )
        text = _complete(messages).strip()
        if not text:
            raise ValueError("Empty completion from LLM.")
        _cache[key] = text
        return ExplanationResult(text=text, source="llm", cached=False)
    except Exception:
        # Any failure (no network, bad key, rate limit, malformed response) →
        # the demo still works with the deterministic explanation.
        return ExplanationResult(text=fallback, source="fallback", cached=False)


def clear_cache() -> None:
    """Clear the in-memory explanation cache (used in tests)."""
    _cache.clear()
