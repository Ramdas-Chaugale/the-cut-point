"""Natural-language search over the hairstyle knowledge base.

Two pieces, both of which work with no API key:

1. **Retrieval** — a TF-IDF index built over the catalogue, so a free-text
   query can be matched against style names, descriptions and tags. The corpus
   is 21 documents, so an in-process index is the right size; there is no point
   pulling in a vector database for this.

2. **Constraint extraction** — turning "something easy that works with curls"
   into the catalogue's own controlled vocabulary (``maintenance: low``,
   ``hair_type: curly``). An LLM does this when a key is configured, because it
   handles phrasing the keyword table will never cover. When it is not
   available, or returns something outside the vocabulary, a deterministic
   synonym table does the same job on the common phrasings.

Results are ranked by both: the constraints filter and boost, the TF-IDF score
orders what is left. Every result carries the reasons it matched, so the UI can
show the user what the query was understood to mean rather than asking them to
trust a black box.
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from functools import lru_cache

from app.core.config import get_settings
from app.knowledge.loader import load_styles
from app.models.recommend import (
    FaceShape,
    HairType,
    Length,
    Maintenance,
    Presentation,
    Style,
)

# Words that carry no signal in a 21-document catalogue of haircuts.
_STOPWORDS = frozenset(
    """
    a an and are as at be but by for from has have i in is it its me my of on or
    something that the their them there they this to want wants with would you
    your like looking look want need
    """.split()
)

_WORD = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> list[str]:
    return [w for w in _WORD.findall(text.lower()) if w not in _STOPWORDS and len(w) > 1]


def _document(style: Style) -> str:
    """The searchable text for one style."""
    return " ".join(
        [
            style.name,
            style.description,
            style.length.value,
            style.maintenance.value + " maintenance",
            " ".join(h.value for h in style.hair_types),
            " ".join(p.value for p in style.presentations),
            " ".join(f.value for f in style.flattering_for),
            # Tags are hyphenated in the data; split so "low-upkeep" also
            # matches a query that says "upkeep".
            " ".join(t.replace("-", " ") for t in style.rationale_tags),
        ]
    )


@dataclass(frozen=True)
class _Index:
    """A TF-IDF index over the catalogue."""

    idf: dict[str, float]
    vectors: dict[str, dict[str, float]]  # style id -> unit-normalised vector


@lru_cache
def _index() -> _Index:
    styles = load_styles()
    docs = {s.id: _tokens(_document(s)) for s in styles}
    n = len(docs)

    seen: Counter[str] = Counter()
    for toks in docs.values():
        seen.update(set(toks))
    # Smoothed IDF, so a term in every document still has a small weight.
    idf = {term: math.log((n + 1) / (df + 1)) + 1.0 for term, df in seen.items()}

    vectors: dict[str, dict[str, float]] = {}
    for style_id, toks in docs.items():
        tf = Counter(toks)
        vec = {t: (1 + math.log(c)) * idf[t] for t, c in tf.items()}
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        vectors[style_id] = {t: v / norm for t, v in vec.items()}
    return _Index(idf=idf, vectors=vectors)


def lexical_scores(query: str) -> dict[str, float]:
    """Cosine similarity between the query and every style, keyed by style id."""
    index = _index()
    q_tf = Counter(_tokens(query))
    if not q_tf:
        return {}
    q_vec = {t: (1 + math.log(c)) * index.idf.get(t, 1.0) for t, c in q_tf.items()}
    norm = math.sqrt(sum(v * v for v in q_vec.values())) or 1.0
    q_vec = {t: v / norm for t, v in q_vec.items()}

    scores: dict[str, float] = {}
    for style_id, vec in index.vectors.items():
        # Iterate the shorter side; a query is almost always shorter.
        scores[style_id] = sum(w * vec.get(t, 0.0) for t, w in q_vec.items())
    return scores


# --------------------------------------------------------------------------
# Constraint extraction
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Constraints:
    """What a free-text query asked for, in the catalogue's own vocabulary."""

    presentation: Presentation | None = None
    length: Length | None = None
    hair_type: HairType | None = None
    maintenance: Maintenance | None = None
    face_shape: FaceShape | None = None
    source: str = "keywords"  # "llm" | "keywords"

    def describe(self) -> list[str]:
        """Human-readable summary, for showing the user what was understood."""
        out: list[str] = []
        if self.presentation:
            out.append(self.presentation.value)
        if self.length:
            out.append(f"{self.length.value} length")
        if self.hair_type:
            out.append(f"{self.hair_type.value} hair")
        if self.maintenance:
            out.append(f"{self.maintenance.value} maintenance")
        if self.face_shape:
            out.append(f"{self.face_shape.value} face")
        return out


# Phrasings that map onto the controlled vocabulary. Longest phrases are
# checked first so "low maintenance" wins over a bare "low".
_SYNONYMS: dict[str, list[tuple[str, object]]] = {
    "maintenance": [
        ("low maintenance", Maintenance.low),
        ("high maintenance", Maintenance.high),
        ("wash and go", Maintenance.low),
        ("easy to style", Maintenance.low),
        ("no effort", Maintenance.low),
        ("low upkeep", Maintenance.low),
        ("low effort", Maintenance.low),
        ("fuss free", Maintenance.low),
        ("easy", Maintenance.low),
        ("quick", Maintenance.low),
    ],
    "length": [
        ("shoulder length", Length.medium),
        ("very short", Length.short),
        ("grown out", Length.long),
        ("buzz", Length.short),
        ("cropped", Length.short),
        ("crop", Length.short),
        ("short", Length.short),
        ("medium", Length.medium),
        ("mid length", Length.medium),
        ("long", Length.long),
    ],
    "hair_type": [
        ("straight", HairType.straight),
        ("wavy", HairType.wavy),
        ("waves", HairType.wavy),
        ("curly", HairType.curly),
        ("curls", HairType.curly),
        ("coily", HairType.coily),
        ("afro", HairType.coily),
        ("kinky", HairType.coily),
        ("4c", HairType.coily),
    ],
    "presentation": [
        ("masculine", Presentation.masculine),
        ("feminine", Presentation.feminine),
        ("unisex", Presentation.unisex),
        ("androgynous", Presentation.unisex),
        ("mens", Presentation.masculine),
        ("men", Presentation.masculine),
        ("male", Presentation.masculine),
        ("womens", Presentation.feminine),
        ("women", Presentation.feminine),
        ("female", Presentation.feminine),
    ],
}


def _keyword_constraints(query: str) -> Constraints:
    """Deterministic extraction. Always available, no key required."""
    text = " " + re.sub(r"[^a-z0-9]+", " ", query.lower()) + " "
    picked: dict[str, object] = {}
    for field_name, pairs in _SYNONYMS.items():
        for phrase, value in pairs:
            if f" {phrase} " in text:
                picked[field_name] = value
                break

    face_shape = None
    for shape in FaceShape:
        if f" {shape.value} " in text:
            face_shape = shape
            break

    return Constraints(
        presentation=picked.get("presentation"),  # type: ignore[arg-type]
        length=picked.get("length"),  # type: ignore[arg-type]
        hair_type=picked.get("hair_type"),  # type: ignore[arg-type]
        maintenance=picked.get("maintenance"),  # type: ignore[arg-type]
        face_shape=face_shape,
        source="keywords",
    )


_EXTRACT_SYSTEM = (
    "You convert a person's description of the haircut they want into a strict "
    "JSON object. Use only these keys and values:\n"
    '  presentation: "masculine" | "feminine" | "unisex" | null\n'
    '  length: "short" | "medium" | "long" | null\n'
    '  hair_type: "straight" | "wavy" | "curly" | "coily" | null\n'
    '  maintenance: "low" | "medium" | "high" | null\n'
    '  face_shape: "oval" | "round" | "square" | "oblong" | "heart" | '
    '"diamond" | "triangle" | null\n'
    "Use null for anything the person did not clearly state. Do not guess. "
    "Reply with the JSON object and nothing else."
)


def _complete(messages: list[dict[str, str]]) -> str:
    """Call Groq and return the completion text. Isolated for testing."""
    from groq import Groq  # imported lazily so a missing key never blocks import

    settings = get_settings()
    client = Groq(api_key=settings.groq_api_key)
    # JSON mode keeps the extraction parseable; the SDK's overloads do not
    # accept a plain dict for it, hence the one ignore on the call.
    completion = client.chat.completions.create(  # type: ignore[call-overload]
        model=settings.groq_model,
        messages=messages,
        temperature=0.0,
        max_tokens=400,
        response_format={"type": "json_object"},
    )
    return (completion.choices[0].message.content or "").strip()


def _enum_or_none(enum_cls, raw):  # type: ignore[no-untyped-def]
    """Accept a value only if it is in the controlled vocabulary."""
    if raw is None:
        return None
    try:
        return enum_cls(str(raw).strip().lower())
    except ValueError:
        return None


def extract_constraints(query: str) -> Constraints:
    """Parse a free-text query into catalogue constraints.

    The LLM runs first when a key is configured. Anything it returns outside
    the controlled vocabulary is dropped rather than trusted, and any failure
    falls back to the keyword table, so this never raises.
    """
    if not get_settings().llm_enabled:
        return _keyword_constraints(query)

    try:
        raw = _complete(
            [
                {"role": "system", "content": _EXTRACT_SYSTEM},
                {"role": "user", "content": query},
            ]
        )
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("Extraction did not return an object.")
        parsed = Constraints(
            presentation=_enum_or_none(Presentation, data.get("presentation")),
            length=_enum_or_none(Length, data.get("length")),
            hair_type=_enum_or_none(HairType, data.get("hair_type")),
            maintenance=_enum_or_none(Maintenance, data.get("maintenance")),
            face_shape=_enum_or_none(FaceShape, data.get("face_shape")),
            source="llm",
        )
        # An extraction that found nothing is no better than the keyword pass,
        # and the keyword pass may still catch an obvious word.
        if not parsed.describe():
            return _keyword_constraints(query)
        return parsed
    except Exception:
        return _keyword_constraints(query)


# --------------------------------------------------------------------------
# Ranking
# --------------------------------------------------------------------------


@dataclass
class SearchHit:
    style: Style
    score: float
    reasons: list[str] = field(default_factory=list)


def _presentation_ok(style: Style, wanted: Presentation | None) -> bool:
    """Mirror the recommendation engine: a request returns its own set plus unisex."""
    if wanted is None:
        return True
    if wanted is Presentation.unisex:
        return Presentation.unisex in style.presentations
    return wanted in style.presentations or Presentation.unisex in style.presentations


def rank(query: str, constraints: Constraints, limit: int = 8) -> list[SearchHit]:
    """Rank the catalogue against a query and its extracted constraints."""
    lexical = lexical_scores(query)
    hits: list[SearchHit] = []

    for style in load_styles():
        # Presentation is a hard filter; showing a feminine-only cut to someone
        # who asked for a men's style is a worse failure than showing nothing.
        if not _presentation_ok(style, constraints.presentation):
            continue

        reasons: list[str] = []
        boost = 0.0
        if constraints.length and style.length is constraints.length:
            reasons.append(f"{style.length.value} length")
            boost += 0.35
        if constraints.hair_type and constraints.hair_type in style.hair_types:
            reasons.append(f"suits {constraints.hair_type.value} hair")
            boost += 0.35
        if constraints.maintenance and style.maintenance is constraints.maintenance:
            reasons.append(f"{style.maintenance.value} maintenance")
            boost += 0.30
        if constraints.face_shape and constraints.face_shape in style.flattering_for:
            reasons.append(f"flatters {constraints.face_shape.value} faces")
            boost += 0.40

        score = lexical.get(style.id, 0.0) + boost
        if score <= 0.0:
            continue
        hits.append(SearchHit(style=style, score=round(score, 4), reasons=reasons))

    hits.sort(key=lambda h: (-h.score, h.style.name))
    return hits[:limit]


def search(query: str, limit: int = 8) -> tuple[Constraints, list[SearchHit]]:
    """Extract constraints from a free-text query and rank the catalogue."""
    constraints = extract_constraints(query)
    return constraints, rank(query, constraints, limit=limit)


def clear_cache() -> None:
    """Drop the TF-IDF index (used in tests after editing the knowledge base)."""
    _index.cache_clear()
