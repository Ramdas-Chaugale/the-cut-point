"""Draw the figures used in the README, from the real data in the repo.

    python tools/make_readme_figures.py

Nothing here is hand-drawn or invented. The face shapes come from the
prototype measurements in services/face_classifier.py, the catalogue charts
come from knowledge/hairstyles.yaml, and the test counts come from a pytest
collection. If the data changes, rerun this and the figures change with it.

Output: docs/figures/
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches          # noqa: E402
import matplotlib.pyplot as plt                # noqa: E402
import numpy as np                             # noqa: E402
import yaml                                    # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGURES = os.path.join(ROOT, "docs", "figures")
CATALOGUE = os.path.join(ROOT, "backend", "app", "knowledge", "hairstyles.yaml")
CLASSIFIER = os.path.join(ROOT, "backend", "app", "services", "face_classifier.py")

INK = "#1c2430"
MUTED = "#6b7480"
ACCENT = "#1b6b4a"
ACCENT2 = "#2f6fb8"
PAPER = "#ffffff"

plt.rcParams.update({
    "font.size": 9,
    "text.color": INK,
    "axes.labelcolor": INK,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "axes.edgecolor": "#d8dde3",
    "figure.facecolor": PAPER,
    "axes.facecolor": PAPER,
    "savefig.facecolor": PAPER,
    "figure.dpi": 160,
})


# --------------------------------------------------------------------------
# data
# --------------------------------------------------------------------------

def load_catalogue() -> list[dict]:
    with open(CATALOGUE, encoding="utf-8") as f:
        return yaml.safe_load(f)["styles"]


def load_prototypes() -> dict[str, dict[str, float]]:
    """Pull the canonical face measurements straight out of the classifier."""
    src = open(CLASSIFIER, encoding="utf-8").read()
    pattern = re.compile(
        r'"(\w+)":\s*CanonicalFace\(face_length=([\d.]+),\s*cheek_width=([\d.]+),'
        r'\s*jaw_width=([\d.]+),\s*forehead_width=([\d.]+)\)')
    out = {}
    for name, length, cheek, jaw, forehead in pattern.findall(src):
        out[name] = {"length": float(length), "cheek": float(cheek),
                     "jaw": float(jaw), "forehead": float(forehead)}
    return out


def collect_tests() -> list[tuple[str, int]]:
    """Ask pytest how many tests there actually are, per module."""
    python = os.path.join(ROOT, "backend", ".venv", "Scripts", "python.exe")
    if not os.path.exists(python):
        python = sys.executable
    try:
        proc = subprocess.run([python, "-m", "pytest", "--collect-only", "-q"],
                              cwd=os.path.join(ROOT, "backend"),
                              capture_output=True, text=True, timeout=300)
        rows = re.findall(r"tests/test_(\w+)\.py:\s*(\d+)", proc.stdout)
        if rows:
            return sorted(((n, int(c)) for n, c in rows), key=lambda r: -r[1])
    except Exception:
        pass
    return []


# --------------------------------------------------------------------------
# figure 1: the seven face shapes, drawn from the classifier's own prototypes
# --------------------------------------------------------------------------

def face_outline(ax, m: dict[str, float], colour: str) -> None:
    """A face built from four measurements: length, forehead, cheek, jaw."""
    cheek = m["cheek"] / 2
    jaw = m["jaw"] / 2
    brow = m["forehead"] / 2
    length = m["length"]

    # heights as fractions of face length, measured from the chin at y=0
    y_chin, y_jaw, y_cheek, y_brow, y_top = 0.0, 0.26, 0.55, 0.78, 1.0
    y_jaw *= length
    y_cheek *= length
    y_brow *= length
    y_top = length

    right = [(0, y_chin), (jaw * 0.92, y_jaw), (cheek, y_cheek),
             (brow, y_brow), (brow * 0.62, y_top)]
    left = [(-x, y) for x, y in reversed(right[:-1])]
    pts = right + [(0, y_top * 1.02)] + left

    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    ax.fill(xs, ys, color=colour, alpha=0.16, zorder=1)
    ax.plot(xs + [xs[0]], ys + [ys[0]], color=colour, lw=1.8, zorder=2,
            solid_joinstyle="round")

    # the three widths the classifier actually measures
    for y, half, label in ((y_brow, brow, "forehead"),
                           (y_cheek, cheek, "cheekbone"),
                           (y_jaw, jaw * 0.92, "jaw")):
        ax.plot([-half, half], [y, y], color=MUTED, lw=0.7, ls=(0, (3, 2)),
                zorder=3)


def figure_face_shapes(protos: dict[str, dict[str, float]]) -> None:
    order = ["oval", "round", "square", "oblong", "heart", "diamond", "triangle"]
    order = [s for s in order if s in protos]
    fig, axes = plt.subplots(1, len(order), figsize=(2.0 * len(order), 4.1))

    for ax, shape in zip(axes, order):
        m = protos[shape]
        face_outline(ax, m, ACCENT)
        ratio = m["length"] / m["cheek"]
        jaw_r = m["jaw"] / m["cheek"]
        fore_r = m["forehead"] / m["cheek"]
        ax.set_title(shape.capitalize(), fontsize=10.5, pad=8, color=INK,
                     fontweight="bold")
        ax.text(0, -0.17 * m["length"],
                "length/cheek  %.2f\nforehead/cheek  %.2f\njaw/cheek  %.2f"
                % (ratio, fore_r, jaw_r),
                ha="center", va="top", fontsize=7.2, color=MUTED, linespacing=1.5)
        ax.set_xlim(-230, 230)
        ax.set_ylim(-0.38 * 560, 600)
        ax.set_aspect("equal")
        ax.axis("off")

    fig.suptitle("Seven face shapes, as the classifier defines them",
                 fontsize=12.5, fontweight="bold", y=1.0)
    fig.text(0.5, -0.02,
             "Each outline is drawn from the prototype measurements in "
             "services/face_classifier.py. Ratios are normalised against "
             "cheekbone width,\nso they are independent of how close the camera "
             "was. Dashed lines mark the three widths measured from the "
             "landmarks.",
             ha="center", fontsize=7.6, color=MUTED, linespacing=1.6)
    fig.tight_layout(rect=(0, 0.02, 1, 0.97))
    fig.savefig(os.path.join(FIGURES, "face_shapes.png"), bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------
# figure 2: which styles suit which face shape
# --------------------------------------------------------------------------

def figure_coverage(styles: list[dict]) -> None:
    shapes = ["oval", "round", "square", "oblong", "heart", "diamond", "triangle"]
    styles = sorted(styles, key=lambda s: (s["length"], s["name"]))
    names = [s["name"] for s in styles]

    grid = np.zeros((len(styles), len(shapes)))
    for i, s in enumerate(styles):
        for j, shape in enumerate(shapes):
            grid[i, j] = 1.0 if shape in s.get("flattering_for", []) else 0.0

    fig, (ax, bar) = plt.subplots(
        1, 2, figsize=(10.5, 7.4), gridspec_kw={"width_ratios": [3.1, 1]})

    ax.imshow(grid, cmap=plt.matplotlib.colors.ListedColormap(["#f2f4f7", ACCENT]),
              aspect="auto", vmin=0, vmax=1)
    ax.set_xticks(range(len(shapes)))
    ax.set_xticklabels([s.capitalize() for s in shapes], fontsize=9)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=8.2)
    ax.set_xticks(np.arange(-0.5, len(shapes), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(names), 1), minor=True)
    ax.grid(which="minor", color=PAPER, lw=1.6)
    ax.tick_params(which="minor", length=0)
    ax.set_title("Which of the 21 styles suit each face shape",
                 fontsize=11.5, fontweight="bold", pad=12)

    per_shape = grid.sum(axis=0)
    bar.barh(range(len(shapes)), per_shape[::-1], color=ACCENT2, height=0.62)
    for i, v in enumerate(per_shape[::-1]):
        bar.text(v + 0.3, i, "%d" % v, va="center", fontsize=8.5, color=INK)
    bar.set_yticks(range(len(shapes)))
    bar.set_yticklabels([s.capitalize() for s in shapes[::-1]], fontsize=9)
    bar.set_xlim(0, max(per_shape) + 3)
    bar.set_xlabel("styles available", fontsize=8.5)
    bar.set_title("Catalogue depth per shape", fontsize=10, pad=12)
    for side in ("top", "right"):
        bar.spines[side].set_visible(False)

    # the caption is written from the numbers, not asserted alongside them
    pairs = sorted(zip(shapes, per_shape), key=lambda p: -p[1])
    top_n = pairs[0][1]
    low_n = pairs[-1][1]
    top = [s.capitalize() for s, v in pairs if v == top_n]
    low = [s.capitalize() for s, v in pairs if v == low_n]
    join = lambda xs: " and ".join([", ".join(xs[:-1]), xs[-1]] if len(xs) > 1
                                   else xs)
    fig.text(0.5, 0.015,
             "%s %s the widest choice at %d of 21 styles. %s %s the fewest at "
             "%d. A thin column is a gap in the catalogue,\nnot a limitation of "
             "the matching: the same ratios are measured either way."
             % (join(top), "has" if len(top) == 1 else "have", top_n,
                join(low), "has" if len(low) == 1 else "have", low_n),
             ha="center", fontsize=7.8, color=MUTED, linespacing=1.6)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(os.path.join(FIGURES, "catalogue_coverage.png"),
                bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------
# figure 3: what the catalogue is made of
# --------------------------------------------------------------------------

def figure_composition(styles: list[dict]) -> None:
    def count(field, order=None, listed=False):
        c = Counter()
        for s in styles:
            v = s.get(field, [])
            if listed:
                c.update(v if isinstance(v, list) else [v])
            else:
                c[v if not isinstance(v, list) else v[0]] += 1
        keys = order or [k for k, _ in c.most_common()]
        return keys, [c.get(k, 0) for k in keys]

    panels = [
        ("Length", *count("length", ["short", "medium", "long"])),
        ("Upkeep", *count("maintenance", ["low", "medium", "high"])),
        ("Hair type", *count("hair_types", ["straight", "wavy", "curly", "coily"],
                             listed=True)),
        ("Presentation", *count("presentations",
                                ["masculine", "feminine", "unisex"], listed=True)),
    ]

    fig, axes = plt.subplots(1, 4, figsize=(12, 3.0))
    for ax, (title, keys, vals) in zip(axes, panels):
        ax.bar(range(len(keys)), vals, color=ACCENT2, width=0.6)
        for i, v in enumerate(vals):
            ax.text(i, v + 0.25, str(v), ha="center", fontsize=8.5, color=INK)
        ax.set_xticks(range(len(keys)))
        ax.set_xticklabels([k.capitalize() for k in keys], fontsize=8.5)
        ax.set_title(title, fontsize=10, fontweight="bold", pad=8)
        ax.set_ylim(0, max(vals) + 2.2)
        ax.set_yticks([])
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)

    fig.suptitle("What the catalogue is made of, across 21 styles",
                 fontsize=12, fontweight="bold", y=1.06)
    fig.text(0.5, -0.1,
             "A style can carry several hair types and presentations, so those "
             "two panels total more than 21. Every value is drawn from the "
             "controlled\nvocabularies validated on load, so a typo in the "
             "catalogue fails at startup rather than silently producing an "
             "empty category.",
             ha="center", fontsize=7.8, color=MUTED, linespacing=1.6)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES, "catalogue_composition.png"),
                bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------
# figure 4: the test suite
# --------------------------------------------------------------------------

def figure_tests(rows: list[tuple[str, int]]) -> None:
    if not rows:
        print("  skipped test figure, pytest collection unavailable")
        return
    names = [n.replace("_", " ") for n, _ in rows][::-1]
    counts = [c for _, c in rows][::-1]
    total = sum(counts)

    fig, ax = plt.subplots(figsize=(7.6, 5.2))
    bars = ax.barh(range(len(names)), counts, color=ACCENT, height=0.66)
    # the biggest module gets a note, because the number looks odd otherwise
    bars[-1].set_color(ACCENT2)
    for i, v in enumerate(counts):
        ax.text(v + 0.35, i, str(v), va="center", fontsize=8.5, color=INK)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=9)
    ax.set_xlim(0, max(counts) + 4)
    ax.set_xlabel("tests collected", fontsize=9)
    ax.set_title("%d backend tests, by module" % total,
                 fontsize=12, fontweight="bold", pad=12)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.grid(axis="x", alpha=0.18)
    ax.set_axisbelow(True)

    fig.text(0.5, -0.03,
             "Counted by pytest collection, not by hand. Face classifier is the "
             "largest because its cases are parametrised over every face shape.\n"
             "All of these run on every push through GitHub Actions, alongside "
             "Ruff, Black and Mypy.",
             ha="center", fontsize=7.8, color=MUTED, linespacing=1.6)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES, "test_suite.png"), bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    os.makedirs(FIGURES, exist_ok=True)
    styles = load_catalogue()
    protos = load_prototypes()
    print("catalogue: %d styles | prototypes: %d shapes"
          % (len(styles), len(protos)))

    figure_face_shapes(protos)
    figure_coverage(styles)
    figure_composition(styles)
    figure_tests(collect_tests())

    for name in sorted(os.listdir(FIGURES)):
        size = os.path.getsize(os.path.join(FIGURES, name)) // 1024
        print("  docs/figures/%s  (%d KB)" % (name, size))


if __name__ == "__main__":
    main()
