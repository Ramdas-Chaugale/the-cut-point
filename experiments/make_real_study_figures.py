"""Draw the real-photograph study figure from results/real_face_study.json.

    python experiments/make_real_study_figures.py

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
DATA = os.path.join(ROOT, "results", "real_face_study.json")

INK, MUTED = "#1c2430", "#6b7480"
RULES, LEARNED, GREY = "#9a7b3f", "#1b6b4a", "#c6ccd3"
WARN = "#a8432f"

plt.rcParams.update({
    "font.size": 9, "text.color": INK, "axes.labelcolor": INK,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.edgecolor": "#d8dde3",
    "figure.facecolor": "white", "axes.facecolor": "white",
    "savefig.facecolor": "white", "figure.dpi": 160,
})

SHORT = {
    "rules as shipped (7 shapes)": "rules as shipped",
    "rules as shipped (5 shapes only)": "rules, 5 shapes only",
    "rules, real centres": "rules, real centres",
    "rules, real centres and scales": "rules, recalibrated",
    "always most common": "always most common",
}


def colour_for(name: str) -> str:
    if "most common" in name:
        return GREY
    if "rules" in name:
        return RULES
    return LEARNED


def panel_accuracy(ax, d: dict) -> None:
    rows = sorted(d["test"].items(), key=lambda kv: kv[1]["accuracy"])
    names = [SHORT.get(k, k) for k, _ in rows]
    accs = [v["accuracy"] for _, v in rows]
    y = np.arange(len(names))

    ax.barh(y, accs, color=[colour_for(k) for k, _ in rows], height=0.62)
    for yi, (k, v) in zip(y, rows):
        label = "%.3f" % v["accuracy"]
        # how badly it piles onto one answer, said plainly next to the number
        share = v["collapse"]["largest_share"]
        if share > 0.6:
            label += "   %.0f%% of answers are “%s”" % (
                100 * share, v["collapse"]["most_predicted"])
        ax.text(v["accuracy"] + 0.008, yi, label,
                va="center", fontsize=8.3, color=INK)

    cnn = d["literature_for_context"]["InceptionV3 on pixels (published)"]
    ax.axvline(cnn, color=WARN, lw=1.3, ls="--")
    ax.text(cnn - 0.012, len(names) - 0.4,
            "published CNN on pixels %.3f" % cnn, rotation=90,
            ha="right", va="top", fontsize=7.6, color=WARN)

    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=8.5)
    ax.set_xlim(0, max(max(accs), cnn) + 0.34)
    ax.set_xlabel("accuracy on %d held-out real faces" % d["n_test"])
    ax.set_title("On real photographs the shipped rules answer\n"
                 "one shape for almost every face",
                 fontsize=11, fontweight="bold", pad=10, loc="left")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="x", alpha=0.18)
    ax.set_axisbelow(True)


def panel_calibration(ax, d: dict) -> None:
    classes = d["classes"]
    gap = d["calibration_gap"]
    real = [gap[c]["real_median"]["length_to_width"] for c in classes]
    proto = [gap[c]["shipped_prototype"]["length_to_width"] for c in classes]
    y = np.arange(len(classes))

    for yi, r, p in zip(y, real, proto):
        ax.plot([r, p], [yi, yi], color=GREY, lw=1.6, zorder=0)
    ax.scatter(real, y, s=46, color=LEARNED, zorder=3, label="real faces (median)")
    ax.scatter(proto, y, s=46, color=RULES, marker="D", zorder=3,
               label="shipped prototype")

    ax.set_yticks(y)
    ax.set_yticklabels(classes, fontsize=9)
    ax.set_xlabel("length to width")
    ax.set_title("The prototypes sit where no real face does",
                 fontsize=11, fontweight="bold", pad=10, loc="left")
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="x", alpha=0.18)
    ax.set_axisbelow(True)

    rs = d["length_to_width_spread"]
    ax.text(0.5, -0.28,
            "Real faces span %.2f of this measurement.\n"
            "The prototypes assume a span of %.2f, %.0f times wider."
            % (rs["real_faces"]["range"], rs["shipped_prototypes"]["range"],
               rs["shipped_prototypes"]["range"] / rs["real_faces"]["range"]),
            transform=ax.transAxes, ha="center", va="top",
            fontsize=8, color=MUTED, linespacing=1.5)


def panel_snr(ax, d: dict) -> None:
    snr = d["signal_to_noise"]
    names = list(snr)
    vals = [snr[n]["ratio"] for n in names]
    order = np.argsort(vals)
    names = [names[i] for i in order]
    vals = [vals[i] for i in order]
    y = np.arange(len(names))

    ax.barh(y, vals, color=RULES, height=0.6)
    for yi, v in zip(y, vals):
        ax.text(v + 0.015, yi, "%.2f" % v, va="center", fontsize=8.5, color=INK)
    ax.axvline(1.0, color=WARN, lw=1.3, ls="--")
    ax.text(1.0, -0.72, "1.0, separation equals noise", fontsize=7.6,
            color=WARN, ha="center")

    ax.set_yticks(y)
    ax.set_yticklabels([n.replace("_", " ") for n in names], fontsize=8.5)
    ax.set_xlim(0, max(max(vals) + 0.22, 1.15))
    ax.set_xlabel("class separation divided by within-class spread")
    ax.set_title("Every measurement overlaps more\nthan it separates",
                 fontsize=11, fontweight="bold", pad=10, loc="left")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="x", alpha=0.18)
    ax.set_axisbelow(True)


def figure(d: dict) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(16.4, 4.3),
                             gridspec_kw={"width_ratios": [1.25, 1, 1]})
    panel_accuracy(axes[0], d)
    panel_calibration(axes[1], d)
    panel_snr(axes[2], d)

    best = d["best_learned"]
    fixed = d["test"]["rules, real centres and scales"]["accuracy"]
    shipped = d["test"]["rules as shipped (5 shapes only)"]["accuracy"]
    learned = d["test"][best]["accuracy"]
    p = d["mcnemar"]["real centres and scales vs shipped"]["p_value"]

    fig.text(0.5, -0.13,
             "Measured on %d real labelled photographs with the app's own geometry code. "
             "Recalibrating the prototypes from real faces lifts the rules from %.3f to "
             "%.3f (p = %.1g); the best learned model on the same five numbers reaches "
             "%.3f.\nAll three sit far below the %.3f a published CNN gets from pixels, "
             "and no single measurement separates the shapes better than its own noise. "
             "Caveat: every image in this dataset is %dx%d, so aspect ratios were forced "
             "and length to width\ncarries an unknown per-image stretch. That means this "
             "cannot separate a weak measurement from one the dataset damaged. "
             "The calibration finding stands either way."
             % (d["n_total"], shipped, fixed, p, learned,
                d["literature_for_context"]["InceptionV3 on pixels (published)"],
                d["aspect_ratio_check"]["sizes"][0]["width"],
                d["aspect_ratio_check"]["sizes"][0]["height"]),
             ha="center", fontsize=7.8, color=MUTED, linespacing=1.6)

    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES, "real_face_study.png"),
                bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    os.makedirs(FIGURES, exist_ok=True)
    with open(DATA, encoding="utf-8") as f:
        d = json.load(f)
    figure(d)
    p = os.path.join(FIGURES, "real_face_study.png")
    print("  docs/figures/real_face_study.png  (%d KB)"
          % (os.path.getsize(p) // 1024))


if __name__ == "__main__":
    main()
