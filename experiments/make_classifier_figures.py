"""Draw the classifier study figures from results/face_classifier_study.json.

    python experiments/make_classifier_figures.py

Reads only that file. Nothing is drawn by hand.
"""

from __future__ import annotations

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
import numpy as np                       # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGURES = os.path.join(ROOT, "docs", "figures")
DATA = os.path.join(ROOT, "results", "face_classifier_study.json")

INK, MUTED = "#1c2430", "#6b7480"
RULES, LEARNED, GREY = "#9a7b3f", "#1b6b4a", "#c6ccd3"

plt.rcParams.update({
    "font.size": 9, "text.color": INK, "axes.labelcolor": INK,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.edgecolor": "#d8dde3",
    "figure.facecolor": "white", "axes.facecolor": "white",
    "savefig.facecolor": "white", "figure.dpi": 160,
})


def figure(d: dict) -> None:
    fig, (ax, ax2) = plt.subplots(
        1, 2, figsize=(11.4, 4.0), gridspec_kw={"width_ratios": [1.15, 1]})

    # left: accuracy, baseline highlighted
    rows = sorted(d["test"].items(), key=lambda kv: kv[1]["accuracy"])
    names = [k for k, _ in rows]
    accs = [v["accuracy"] for _, v in rows]
    colours = [RULES if "rules" in n else (GREY if "most common" in n else LEARNED)
               for n in names]

    y = np.arange(len(names))
    ax.barh(y, accs, color=colours, height=0.62)
    for yi, a in zip(y, accs):
        ax.text(a + 0.008, yi, "%.3f" % a, va="center", fontsize=9, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=9)
    ax.set_xlim(0, max(accs) + 0.12)
    ax.set_xlabel("accuracy on %d held-out faces" % d["n_test"])
    ax.set_title("Learned boundaries against the shipped rules",
                 fontsize=11.5, fontweight="bold", pad=10)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="x", alpha=0.18)
    ax.set_axisbelow(True)

    mc = d["mcnemar"]
    ax.text(0.015, 0.03,
            "McNemar, paired on the same faces:  p = %.2g" % mc["p_value"],
            transform=ax.transAxes, fontsize=8.5,
            color=LEARNED if mc["significant_at_05"] else MUTED)

    # right: does the advantage survive detector error
    sweep = d["noise_sweep"]
    noise = [r["noise"] * 100 for r in sweep]
    for key, colour, lw in (("rules", RULES, 2.2),
                            (d["best_learned"], LEARNED, 2.2)):
        ax2.plot(noise, [r[key] for r in sweep], marker="o", ms=4,
                 color=colour, lw=lw, label=key)
    for key in sweep[0]:
        if key in ("noise", "rules", d["best_learned"]):
            continue
        ax2.plot(noise, [r[key] for r in sweep], color=GREY, lw=1.0,
                 zorder=0)

    ax2.set_xlabel("landmark error, % of image width")
    ax2.set_ylabel("accuracy")
    ax2.set_title("Both degrade together as the detector gets noisier",
                  fontsize=11, fontweight="bold", pad=10)
    ax2.legend(frameon=False, fontsize=8.5)
    for s in ("top", "right"):
        ax2.spines[s].set_visible(False)
    ax2.grid(alpha=0.18)
    ax2.set_axisbelow(True)

    gap = d["test"][d["best_learned"]]["accuracy"] - d["test"]["rules (shipped)"]["accuracy"]
    fig.text(0.5, -0.07,
             "A trained model wins by %.1f points and the difference is real, "
             "but it is modest, and the rules need no training data and can be "
             "explained to a user.\nFaces are generated from the same seven "
             "prototypes the rules use, with %d%% jitter, so this measures "
             "learned boundaries against hand-set weights. It is not evidence "
             "about real photographs."
             % (gap * 100, int(d["jitter"] * 100)),
             ha="center", fontsize=7.8, color=MUTED, linespacing=1.6)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES, "classifier_study.png"),
                bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    os.makedirs(FIGURES, exist_ok=True)
    with open(DATA, encoding="utf-8") as f:
        d = json.load(f)
    figure(d)
    p = os.path.join(FIGURES, "classifier_study.png")
    print("  docs/figures/classifier_study.png  (%d KB)"
          % (os.path.getsize(p) // 1024))


if __name__ == "__main__":
    main()
