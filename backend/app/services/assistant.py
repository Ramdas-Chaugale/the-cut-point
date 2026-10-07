"""A stylist assistant grounded in the hairstyle knowledge base.

This is retrieval-augmented generation over a small, curated corpus. The
catalogue is the only source the model is given, and the styles it drew from
come back with the answer so the user can check it. That matters more here
than it would in a general chatbot: an ungrounded model will happily invent a
haircut that no salon in the list actually offers.

As everywhere else in this codebase, the LLM is optional. With no key the
retrieval still runs and the answer is assembled from the catalogue entries
themselves, which is less fluent but never wrong.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import get_settings
from app.knowledge.loader import load_styles
from app.models.recommend import FaceShape, Style
from app.services.style_search import lexical_scores

# How many catalogue entries to put in front of the model. Four is enough to
# answer a comparison question without burying the relevant one.
_TOP_K = 4

_SYSTEM = (
    "You are a hairstylist answering a client's question. You are given a list "
    "of hairstyles from the salon's catalogue. Use only those entries: do not "
    "mention any haircut that is not listed, and do not invent details about "
    "the ones that are. If the catalogue does not answer the question, say so "
    "plainly and suggest the closest listed style. Reply in at most three "
    "short sentences, in plain prose with no lists or markdown."
)


@dataclass(frozen=True)
class AssistantAnswer:
    text: str
    sources: tuple[Style, ...]
    source: str  # "llm" | "fallback"


def retrieve(question: str, face_shape: FaceShape | None = None, k: int = _TOP_K) -> list[Style]:
    """The catalogue entries most relevant to a question."""
    scores = lexical_scores(question)
    styles = load_styles()

    ranked: list[tuple[float, Style]] = []
    for style in styles:
        score = scores.get(style.id, 0.0)
        # A stated face shape is context, not the question, so it nudges the
        # ranking rather than filtering it.
        if face_shape and face_shape in style.flattering_for:
            score += 0.15
        ranked.append((score, style))

    ranked.sort(key=lambda pair: (-pair[0], pair[1].name))
    top = [style for score, style in ranked if score > 0.0][:k]
    # A question with no catalogue overlap at all ("what should I do?") still
    # deserves something to talk about.
    return top or [style for _, style in ranked[:k]]


def _context(styles: list[Style]) -> str:
    lines = []
    for s in styles:
        lines.append(
            f"- {s.name}: {s.description} "
            f"Length {s.length.value}; {s.maintenance.value} maintenance; "
            f"suits {', '.join(h.value for h in s.hair_types)} hair; "
            f"flatters {', '.join(f.value for f in s.flattering_for)} faces."
        )
    return "\n".join(lines)


def _fallback_text(question: str, styles: list[Style], face_shape: FaceShape | None) -> str:
    """Deterministic answer assembled from the retrieved entries."""
    if not styles:
        return (
            "Nothing in the catalogue covers that yet. Try describing the length "
            "or the upkeep you want."
        )

    lead = styles[0]
    shape_note = (
        f" It is listed as flattering for {face_shape.value} faces."
        if (face_shape and face_shape in lead.flattering_for)
        else ""
    )
    others = [s.name for s in styles[1:3]]
    also = f" {' and '.join(others)} are close alternatives." if others else ""
    return (
        f"From the catalogue, the closest match is {lead.name}: {lead.description} "
        f"It is {lead.maintenance.value} maintenance and works with "
        f"{', '.join(h.value for h in lead.hair_types)} hair.{shape_note}{also}"
    )


def _complete(messages: list[dict[str, str]]) -> str:
    """Call Groq and return the completion text. Isolated for testing."""
    from groq import Groq  # imported lazily so a missing key never blocks import

    settings = get_settings()
    client = Groq(api_key=settings.groq_api_key)
    completion = client.chat.completions.create(
        model=settings.groq_model,
        messages=messages,  # type: ignore[arg-type]
        temperature=0.3,
        max_tokens=500,
    )
    return (completion.choices[0].message.content or "").strip()


def ask(question: str, face_shape: FaceShape | None = None) -> AssistantAnswer:
    """Answer a styling question from the catalogue, never raising."""
    styles = retrieve(question, face_shape)
    fallback = _fallback_text(question, styles, face_shape)

    if not get_settings().llm_enabled:
        return AssistantAnswer(text=fallback, sources=tuple(styles), source="fallback")

    shape_line = f"\nThe client's face shape is {face_shape.value}." if face_shape else ""
    user = f"Catalogue:\n{_context(styles)}\n{shape_line}\n" f"Client's question: {question}"

    try:
        text = _complete(
            [{"role": "system", "content": _SYSTEM}, {"role": "user", "content": user}]
        ).strip()
        if not text:
            raise ValueError("Empty completion from LLM.")
        return AssistantAnswer(text=text, sources=tuple(styles), source="llm")
    except Exception:
        return AssistantAnswer(text=fallback, sources=tuple(styles), source="fallback")
