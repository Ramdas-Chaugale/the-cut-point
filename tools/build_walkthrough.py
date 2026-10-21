"""Build notebooks/walkthrough.ipynb from the cell list below, then execute it.

    python tools/build_walkthrough.py

The notebook imports from backend/app and uses parametric faces, so it runs the
real classifier end to end without a single photograph.
"""

from __future__ import annotations

import os
import subprocess
import sys

import nbformat as nbf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "notebooks", "walkthrough.ipynb")

MD, PY = "markdown", "code"

CELLS: list[tuple[str, str]] = [

(MD, """# CutPoint, walked through

Face shape from facial geometry, hairstyle recommendation, and the search behind
the catalogue.

Everything here imports from `backend/app`, so no logic is repeated and nothing
can drift from the code the 139 tests cover. It also runs without a single
photograph, because the classifier can be fed parametric faces built from
measurements.

**Where the numbers come from**

| Step | File | Holds |
|---|---|---|
| Catalogue | `backend/app/knowledge/hairstyles.yaml` | 21 styles with controlled vocabularies, validated on load |
| Geometry | `backend/app/services/face_geometry.py` | four measurements, three ratios |
| Classifier | `backend/app/services/face_classifier.py` | seven prototype faces |
| Ranking | `backend/app/services/recommend.py` | scoring and the reasons |
| Search | `backend/app/services/style_search.py` | TF-IDF over the catalogue |
| Charts | `tools/make_readme_figures.py` | `docs/figures/*.png` |"""),

(PY, """import sys, os
sys.path.insert(0, os.path.abspath('../backend'))

import numpy as np
import matplotlib.pyplot as plt

from app.knowledge.loader import load_styles
from app.services.face_geometry import compute_features
from app.services import face_classifier as fc
from app.services.recommend import recommend
from app.models.recommend import RecommendRequest

plt.rcParams.update({'figure.dpi': 110, 'font.size': 9})
print('ready')"""),

(MD, """## 1. The catalogue

21 styles in a YAML file with controlled vocabularies. A typo fails at startup
rather than quietly producing an empty category, which is the whole reason for
validating on load rather than trusting the file."""),

(PY, """styles = load_styles()
print('%d styles loaded\\n' % len(styles))

s = styles[0]
for field in ('id', 'name', 'presentations', 'length', 'hair_types',
              'maintenance', 'flattering_for', 'rationale_tags'):
    print('%-16s %s' % (field, getattr(s, field, None)))"""),

(MD, """`flattering_for` is what the recommender matches against, and `rationale_tags`
are what turn a match into a written reason rather than a bare score.

## 2. Face shape is measured, not predicted

Detection uses geometric ratios over MediaPipe's 468 facial landmarks: face
length, cheekbone width, jaw width, forehead width, and the jaw angle.

That is deliberate. The ratios are explainable, they need no training data, and
because they measure bone structure rather than hair they stay accurate on bald
and short haired faces, which is exactly where a hair trained classifier fails.

`build_face_landmarks` turns four measurements into a landmark set, which means
the classifier can be exercised without any photo at all. Here is an oval
face."""),

(PY, """oval = fc.CANONICAL_FACES['oval']
print('measurements (pixels)')
for k in ('face_length', 'cheek_width', 'jaw_width', 'forehead_width'):
    print('  %-16s %.0f' % (k, getattr(oval, k)))

landmarks = fc.build_face_landmarks(oval)
feats = compute_features(landmarks, fc._IMAGE, fc._IMAGE)

print('\\nratios, all normalised against cheekbone width')
for k in ('length_to_width', 'forehead_to_cheek', 'jaw_to_cheek', 'forehead_to_jaw'):
    print('  %-20s %.3f' % (k, getattr(feats, k)))"""),

(MD, """Normalising against cheekbone width is what makes this independent of how close
the camera was. A face photographed from two metres and from half a metre gives
the same ratios.

## 3. Does the classifier recover its own prototypes?

The obvious first check. Build each of the seven prototype faces, run the real
classifier, and see what comes back."""),

(PY, """shapes = ['oval', 'round', 'square', 'oblong', 'heart', 'diamond', 'triangle']

print('%-10s %-10s %10s' % ('built as', 'classified', 'confidence'))
print('-' * 34)
correct = 0
for name in shapes:
    lm = fc.build_face_landmarks(fc.CANONICAL_FACES[name])
    res = fc.classify(compute_features(lm, fc._IMAGE, fc._IMAGE))
    ok = res.shape == name
    correct += ok
    print('%-10s %-10s %9.2f  %s' % (name, res.shape, res.confidence, '' if ok else '<- wrong'))

print('\\n%d of %d recovered' % (correct, len(shapes)))"""),

(MD, """Seven out of seven, which is the least it could do. A prototype failing to
classify as itself would mean the feature vector and the distance function
disagree.

This is a sanity check rather than evidence of accuracy. The interesting question
is what happens when a face is **not** a textbook example.

## 4. What happens between two shapes

Real faces sit between the prototypes. Here is a face morphed continuously from
round to oblong, with everything else held fixed."""),

(PY, """round_f, oblong_f = fc.CANONICAL_FACES['round'], fc.CANONICAL_FACES['oblong']
steps = np.linspace(0, 1, 21)

rows = []
for t in steps:
    face = fc.CanonicalFace(
        face_length   = round_f.face_length   * (1-t) + oblong_f.face_length   * t,
        cheek_width   = round_f.cheek_width   * (1-t) + oblong_f.cheek_width   * t,
        jaw_width     = round_f.jaw_width     * (1-t) + oblong_f.jaw_width     * t,
        forehead_width= round_f.forehead_width* (1-t) + oblong_f.forehead_width* t)
    lm = fc.build_face_landmarks(face)
    f = compute_features(lm, fc._IMAGE, fc._IMAGE)
    res = fc.classify(f)
    rows.append((t, f.length_to_width, res.shape, res.confidence))

print('%6s %10s  %-10s %s' % ('morph', 'len/cheek', 'called it', 'confidence'))
print('-' * 44)
for t, ratio, shape, conf in rows[::2]:
    print('%6.2f %10.2f  %-10s %.2f' % (t, ratio, shape, conf))"""),

(PY, """fig, ax = plt.subplots(figsize=(7.5, 3.2))
ts   = [r[0] for r in rows]
conf = [r[3] for r in rows]
shape_at = [r[2] for r in rows]

boundaries = [i for i in range(1, len(shape_at)) if shape_at[i] != shape_at[i-1]]
ax.plot(ts, conf, color='#1b6b4a', lw=1.8)
for b in boundaries:
    ax.axvline(ts[b], color='#b3482f', ls=(0,(4,3)), lw=1.4)
    ax.text(ts[b], max(conf)*0.99, ' %s to %s' % (shape_at[b-1], shape_at[b]),
            fontsize=8, color='#b3482f', va='top', rotation=90)
ax.set_xlabel('morph from round (0) to oblong (1)')
ax.set_ylabel('confidence')
ax.set_title('Confidence dips wherever the classifier changes its mind', fontsize=11)
for s in ('top','right'): ax.spines[s].set_visible(False)
ax.grid(alpha=.2); plt.tight_layout(); plt.show()"""),

(MD, """Confidence is lowest right where the classifier changes its mind, which is what
it should do. A face genuinely on the boundary between two shapes is not a
confident call, and the number says so rather than hiding it.

That matters for the product: a borderline face can be shown styles from both
shapes instead of being forced into one.

## 5. From a shape to a recommendation

Ranking scores each style against the detected shape and the stated preferences,
and reports which preferences it satisfied. Nothing is a black box."""),

(PY, """req = RecommendRequest(face_shape='round', presentation='masculine',
                       desired_length='short', maintenance='low', limit=5)
res = recommend(req)

for i, item in enumerate(res.recommendations, 1):
    print('%d. %-24s match %.2f   %s / %s upkeep'
          % (i, item.name, item.match_score, item.length.value, item.maintenance.value))
    print('      satisfied : %s' % ', '.join(item.matched_on))
    print('      why it works: %s' % ', '.join(item.rationale_tags))
    print()"""),

(MD, """Every result carries its reasons. That is the difference between a recommender a
user trusts and one they argue with.

## 6. How much choice each shape actually gets

A fair question to ask of any catalogue: is it equally useful to everyone?"""),

(PY, """per_shape = {sh: sum(sh in st.flattering_for for st in styles) for sh in shapes}
order = sorted(per_shape.items(), key=lambda kv: -kv[1])

fig, ax = plt.subplots(figsize=(6.4, 3.0))
ax.bar([k.capitalize() for k, _ in order], [v for _, v in order], color='#2f6fb8')
for i, (_, v) in enumerate(order):
    ax.text(i, v + 0.25, str(v), ha='center', fontsize=9)
ax.set_ylabel('styles available of %d' % len(styles))
ax.set_ylim(0, max(per_shape.values()) + 2.5)
for s in ('top','right','left'): ax.spines[s].set_visible(False)
ax.set_yticks([]); plt.tight_layout(); plt.show()

top, low = order[0], order[-1]
print('%s has the widest choice at %d of %d.' % (top[0].capitalize(), top[1], len(styles)))
print('%s has the fewest at %d.' % (low[0].capitalize(), low[1]))
print()
print('A thin column is a gap in the catalogue, not a weakness in the matching.')
print('The same ratios are measured either way.')"""),

(MD, """## 7. Search, and why there is no vector database

A free text query is turned into the catalogue's own controlled vocabulary, then
retrieval runs over a TF-IDF index built at startup.

The index covers **21 documents**. A vector database would be weight without
benefit at that size, and it would add a service to deploy and keep alive. This
is the kind of decision worth making explicitly rather than by habit."""),

(PY, """from app.services.style_search import _tokens

doc = '%s %s %s %s' % (styles[0].name, styles[0].description,
                       ' '.join(styles[0].hair_types),
                       ' '.join(styles[0].rationale_tags))
print('a catalogue document, tokenised:')
print(' ', _tokens(doc)[:18], '...')
print()
print('corpus size: %d documents' % len(styles))
print('a TF-IDF index over 21 documents fits in memory and needs no service.')"""),

(MD, """## 8. Privacy is a design decision, not a policy page

Landmark detection runs in the browser using MediaPipe. The backend receives
derived ratios, never a photograph, unless the user explicitly asks for a server
side try on, and then it receives only that one image.

The whole of this notebook is a demonstration of why that is possible: the
classifier never needs a photo, only four measurements.

## 9. What this does not do

- The 2D try on is a landmark anchored overlay, not a neural render.
- The four angle views are reference images of each hairstyle, not a
  reconstruction of the user's own head. A single front photo cannot give a real
  back of head view, so the app does not invent one.
- Face shape prototypes are anthropometric reference values, not a population
  study. They classify consistently. They are not a clinical measurement.
- A single primary face is assumed, with specific messaging for no face,
  multiple faces, low quality and non frontal photos.

---

**To run the whole thing:**

```bash
docker compose up -d
cd backend && uvicorn app.main:app --reload
cd frontend && npm run dev
pytest -q                            # 139 passed
```""")
]


def build() -> None:
    nb = nbf.v4.new_notebook()
    nb.cells = [nbf.v4.new_markdown_cell(s) if k == MD else nbf.v4.new_code_cell(s)
                for k, s in CELLS]
    nb.metadata = {
        "kernelspec": {"display_name": "Python 3", "language": "python",
                       "name": "python3"},
        "language_info": {"name": "python", "version": sys.version.split()[0]},
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    print("wrote %s (%d cells)" % (os.path.relpath(OUT, ROOT), len(nb.cells)))


def execute() -> None:
    venv = os.path.join(ROOT, "backend", ".venv", "Scripts", "python.exe")
    python = venv if os.path.exists(venv) else sys.executable
    cmd = [python, "-m", "nbconvert", "--to", "notebook", "--execute",
           "--inplace", "--ExecutePreprocessor.timeout=600", OUT]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-3000:])
        raise SystemExit("execution failed")
    print("executed cleanly")


if __name__ == "__main__":
    build()
    execute()
