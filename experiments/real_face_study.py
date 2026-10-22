"""Do the shipped rules work on real photographs, and can they be fixed?

    python experiments/real_face_features.py --per-class 400
    python experiments/real_face_study.py

The earlier study (face_classifier_study.py) generated faces from the same seven
prototypes the rules use, so it could only ask whether learned boundaries beat
hand-set weights on that distribution. It said so, and said it was not evidence
about real photographs.

This is that evidence. It measures real labelled photographs with the app's own
geometry code and asks three things:

    1. how well do the shipped rules do on real faces
    2. how much of any failure is the prototypes being miscalibrated,
       rather than the five measurements being uninformative
    3. what do the same measurements support once boundaries are learned

The second question matters most, because a miscalibrated prototype is a bug worth
fixing and an uninformative feature set is a reason to change approach.

Writes results/real_face_study.json
"""

from __future__ import annotations

import csv
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))

from scipy.stats import chi2                                   # noqa: E402
from sklearn.dummy import DummyClassifier                      # noqa: E402
from sklearn.ensemble import RandomForestClassifier            # noqa: E402
from sklearn.linear_model import LogisticRegression            # noqa: E402
from sklearn.metrics import confusion_matrix, f1_score         # noqa: E402
from sklearn.model_selection import train_test_split           # noqa: E402
from sklearn.neural_network import MLPClassifier               # noqa: E402
from sklearn.pipeline import make_pipeline                     # noqa: E402
from sklearn.preprocessing import StandardScaler               # noqa: E402

from app.services import face_classifier as fc                 # noqa: E402

FEATURES = os.path.join(ROOT, "results", "real_face_features.csv")
OUT = os.path.join(ROOT, "results", "real_face_study.json")

# The five the dataset labels. The app also knows diamond and triangle.
CLASSES = ["heart", "oblong", "oval", "round", "square"]
UNLABELLED = [s for s in fc.PROTOTYPES if s not in CLASSES]

FEATURE_NAMES = ["length_to_width", "forehead_to_cheek", "jaw_to_cheek",
                 "forehead_to_jaw", "jaw_angle_deg"]

# Published accuracy on a version of this dataset, for context only. Those
# models read pixels with a CNN; this one reads five numbers. Not reproduced here.
LITERATURE = {
    "features plus gradient boosting (published)": 0.64,
    "InceptionV3 on pixels (published)": 0.796,
    "source": "arxiv.org/pdf/1911.07916 and the repos that use this dataset",
}


def load() -> tuple[np.ndarray, np.ndarray, np.ndarray, list]:
    if not os.path.exists(FEATURES):
        raise SystemExit("run experiments/real_face_features.py first")
    X, y, frontal, sizes = [], [], [], []
    with open(FEATURES, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            X.append([float(row[k]) for k in FEATURE_NAMES])
            y.append(row["label"])
            frontal.append(row["is_frontal"].strip().lower() in ("true", "1"))
            sizes.append((int(row["width"]), int(row["height"])))
    return np.array(X), np.array(y), np.array(frontal), sizes


def aspect_ratio_check(sizes: list) -> dict:
    """Did this dataset resize every image to one shape?

    The features are ratios of pixel distances, so they only mean something if
    pixels are square and the photo was not stretched. If every image has been
    forced to one size regardless of how it was originally framed, then each
    image carries an unknown horizontal-to-vertical stretch, and that lands
    straight on length_to_width. Worth measuring rather than assuming.
    """
    distinct = sorted(set(sizes))
    return {
        "distinct_sizes": len(distinct),
        "sizes": [{"width": w, "height": h, "count": sizes.count((w, h))}
                  for w, h in distinct[:5]],
        "all_one_size": len(distinct) == 1,
        "warning": ("Every image is the same pixel size, so the dataset was "
                    "resized to a fixed frame and the original aspect ratios "
                    "are gone. Any per-image stretch is now baked in and falls "
                    "on the width-to-height measurements, length_to_width worst "
                    "of all. Results from this dataset cannot separate a weak "
                    "feature from a feature this preprocessing damaged."
                    if len(distinct) == 1 else
                    "Image sizes vary, so aspect ratio was not forced."),
    }


def signal_to_noise(X: np.ndarray, y: np.ndarray) -> dict:
    """How much does each measurement separate the classes, against its own noise?

    Spread of the per-class medians, divided by the pooled within-class spread.
    Below about 1 means the classes overlap more than they separate, so no
    classifier reading only that number can do much with it.
    """
    out = {}
    for i, name in enumerate(FEATURE_NAMES):
        meds = [float(np.median(X[y == c][:, i])) for c in CLASSES]
        within = float(np.sqrt(np.mean([np.var(X[y == c][:, i], ddof=1)
                                        for c in CLASSES])))
        out[name] = {
            "class_medians": {c: round(m, 3) for c, m in zip(CLASSES, meds)},
            "between_class_spread": round(float(np.std(meds)), 4),
            "within_class_spread": round(within, 4),
            "ratio": round(float(np.std(meds) / within), 3) if within else None,
        }
    return out


def rules_predict(X: np.ndarray, prototypes: dict,
                  scales: tuple | None = None) -> np.ndarray:
    """Nearest prototype under the project's weighted distance.

    scales=None uses the shipped _SCALES. Passing scales swaps in different
    per-feature divisors, which is the second half of the recalibration.
    """
    keys = list(prototypes)
    if scales is None:
        dist = lambda fv, p: fc._weighted_sq_distance(tuple(fv), p)
    else:
        w = np.array(fc._WEIGHTS)
        s = np.array(scales)
        dist = lambda fv, p: float(
            np.sum(w * ((np.asarray(fv) - np.asarray(p)) / s) ** 2))
    out = []
    for fv in X:
        d = {k: dist(fv, prototypes[k]) for k in keys}
        out.append(min(d, key=d.get))
    return np.array(out)


def recalibrate(X: np.ndarray, y: np.ndarray) -> dict:
    """Rebuild the prototypes as the per-class median of real measurements.

    Same rule, same weights, same explainability. Only the reference points move,
    from hand-set guesses to where real faces of each shape actually sit. The
    median rather than the mean, so a bad landmark fit cannot drag a prototype.
    """
    return {c: tuple(np.median(X[y == c], axis=0)) for c in CLASSES}


def real_scales(X: np.ndarray, y: np.ndarray) -> tuple:
    """Per-feature divisors taken from how much real faces actually vary.

    The shipped _SCALES were set for the synthetic spread. Using the pooled
    within-class spread instead makes the distance a diagonal Mahalanobis one,
    so each measurement contributes in proportion to how much it really moves.
    """
    pooled = np.sqrt(np.mean([np.var(X[y == c], axis=0, ddof=1)
                              for c in CLASSES], axis=0))
    return tuple(float(v) if v > 1e-9 else 1.0 for v in pooled)


def collapse(pred: np.ndarray) -> dict:
    """How badly does a classifier pile everything onto one answer?"""
    vals, counts = np.unique(pred, return_counts=True)
    return {
        "classes_used": int(len(vals)),
        "largest_share": float(counts.max() / counts.sum()),
        "most_predicted": str(vals[counts.argmax()]),
        "breakdown": {str(v): int(c) for v, c in zip(vals, counts)},
    }


def mcnemar(a_ok: np.ndarray, b_ok: np.ndarray) -> dict:
    """Paired test on the same faces. a is the baseline, b the challenger."""
    b = int((a_ok & ~b_ok).sum())
    c = int((~a_ok & b_ok).sum())
    stat = (abs(b - c) - 1) ** 2 / (b + c) if (b + c) else 0.0
    p = float(chi2.sf(stat, 1))
    return {"baseline_right_other_wrong": b, "other_right_baseline_wrong": c,
            "statistic": float(stat), "p_value": p, "significant_at_05": p < 0.05}


def acc(pred: np.ndarray, true: np.ndarray) -> float:
    return float((pred == true).mean())


def main() -> None:
    X, y, frontal, sizes = load()
    print("measured faces: %d" % len(X))
    for c in CLASSES:
        print("  %-8s %4d" % (c, int((y == c).sum())))

    aspect = aspect_ratio_check(sizes)
    if aspect["all_one_size"]:
        print("\nCAVEAT: all %d images are %dx%d." % (
            len(sizes), sizes[0][0], sizes[0][1]))
        print("  Aspect ratios were forced, so length_to_width carries an")
        print("  unknown per-image stretch. This limits what follows.")

    X_tr, X_te, y_tr, y_te, _, fr_te = train_test_split(
        X, y, frontal, test_size=0.3, random_state=0, stratify=y)
    print("\ntrain %d | test %d" % (len(X_tr), len(X_te)))

    out: dict = {
        "dataset": "codernotme/face_shape via HuggingFace, five labelled shapes",
        "provenance": ("Photographs of real people, re-hosted by a third party. "
                       "Only measurements derived from them are committed to this "
                       "repo, never the images. The re-host states MIT, which "
                       "cannot govern the underlying photographs, so the images "
                       "are treated as input to measure and not as a "
                       "redistributable asset."),
        "measurements": FEATURE_NAMES,
        "n_total": len(X), "n_train": len(X_tr), "n_test": len(X_te),
        "classes": CLASSES,
        "shapes_app_knows_but_dataset_does_not_label": UNLABELLED,
        "literature_for_context": LITERATURE,
        "aspect_ratio_check": aspect,
        "test": {},
    }

    snr = signal_to_noise(X_tr, y_tr)
    out["signal_to_noise"] = snr
    print("\nhow well each measurement separates the five shapes")
    print("  %-18s %s %8s" % ("", "  ".join("%7s" % c[:6] for c in CLASSES),
                              "sep/noise"))
    for name, d in snr.items():
        print("  %-18s %s %8.2f"
              % (name, "  ".join("%7.3f" % d["class_medians"][c]
                                 for c in CLASSES), d["ratio"]))
    print("  below 1.0 means the shapes overlap more than they separate")

    # ---- the calibration gap, which is the heart of it -------------------
    gap = {}
    for c in CLASSES:
        real = np.median(X_tr[y_tr == c], axis=0)
        proto = np.array(fc.PROTOTYPES[c])
        gap[c] = {
            "shipped_prototype": {k: round(float(v), 3)
                                  for k, v in zip(FEATURE_NAMES, proto)},
            "real_median": {k: round(float(v), 3)
                            for k, v in zip(FEATURE_NAMES, real)},
        }
    out["calibration_gap"] = gap

    lw_real = [float(np.median(X_tr[y_tr == c][:, 0])) for c in CLASSES]
    lw_proto = [float(fc.PROTOTYPES[c][0]) for c in CLASSES]
    out["length_to_width_spread"] = {
        "shipped_prototypes": {"min": round(min(lw_proto), 3),
                               "max": round(max(lw_proto), 3),
                               "range": round(max(lw_proto) - min(lw_proto), 3)},
        "real_faces": {"min": round(min(lw_real), 3),
                       "max": round(max(lw_real), 3),
                       "range": round(max(lw_real) - min(lw_real), 3)},
    }
    print("\nlength-to-width, median of real faces against the shipped prototype")
    for c, r, p in zip(CLASSES, lw_real, lw_proto):
        print("  %-8s real %.2f   prototype %.2f   off by %+.2f" % (c, r, p, p - r))

    # ---- baselines --------------------------------------------------------
    dummy = DummyClassifier(strategy="most_frequent").fit(X_tr, y_tr)
    preds = {"always most common": dummy.predict(X_te)}

    # Strict: the rules as they ship, free to answer diamond or triangle.
    # Those answers cannot be right here, and counting them as wrong is the
    # honest way to score a seven-class rule on a five-class dataset.
    preds["rules as shipped (7 shapes)"] = rules_predict(X_te, fc.PROTOTYPES)

    # Restricted: same rules, choice limited to the five the dataset labels.
    # This is the fair comparison against a five-class learned model.
    five = {c: fc.PROTOTYPES[c] for c in CLASSES}
    preds["rules as shipped (5 shapes only)"] = rules_predict(X_te, five)

    # The fix, in two halves, so the study shows which half earns its keep.
    # Half one: move the reference points to where real faces sit.
    recal = recalibrate(X_tr, y_tr)
    preds["rules, real centres"] = rules_predict(X_te, recal)

    # Half two: also divide each measurement by how much it really varies.
    scales = real_scales(X_tr, y_tr)
    preds["rules, real centres and scales"] = rules_predict(X_te, recal, scales)

    out["recalibrated_prototypes"] = {
        c: {k: round(float(v), 3) for k, v in zip(FEATURE_NAMES, recal[c])}
        for c in CLASSES}
    out["scales"] = {
        "shipped": {k: v for k, v in zip(FEATURE_NAMES, fc._SCALES)},
        "from_real_faces": {k: round(v, 4)
                            for k, v in zip(FEATURE_NAMES, scales)},
    }
    print("\nper-feature scale, shipped against the real spread")
    for k, a, b in zip(FEATURE_NAMES, fc._SCALES, scales):
        print("  %-18s shipped %7.3f   real %7.3f   %.0fx too wide"
              % (k, a, b, a / b if b else 0))

    # ---- learned ----------------------------------------------------------
    models = {
        "logistic regression": make_pipeline(
            StandardScaler(), LogisticRegression(max_iter=4000)),
        "random forest": RandomForestClassifier(n_estimators=400, random_state=0),
        "small MLP": make_pipeline(
            StandardScaler(),
            MLPClassifier(hidden_layer_sizes=(32, 16), max_iter=4000,
                          random_state=0)),
    }
    for name, m in models.items():
        m.fit(X_tr, y_tr)
        preds[name] = m.predict(X_te)

    for name, p in preds.items():
        out["test"][name] = {
            "accuracy": acc(p, y_te),
            "macro_f1": float(f1_score(y_te, p, average="macro",
                                       labels=CLASSES, zero_division=0)),
            "collapse": collapse(p),
        }

    print("\n%-36s %8s %9s %7s %s" % ("", "acc", "macro F1", "classes", "biggest class"))
    print("-" * 82)
    for name, r in sorted(out["test"].items(), key=lambda kv: -kv[1]["accuracy"]):
        print("%-36s %8.3f %9.3f %7d   %s %.0f%%"
              % (name, r["accuracy"], r["macro_f1"],
                 r["collapse"]["classes_used"],
                 r["collapse"]["most_predicted"],
                 100 * r["collapse"]["largest_share"]))

    print("\nfor context, published on a version of this dataset:")
    print("  features plus gradient boosting  0.640")
    print("  InceptionV3 on pixels            0.796   (reads pixels, not 5 numbers)")

    # ---- is the improvement real? ----------------------------------------
    base = preds["rules as shipped (5 shapes only)"] == y_te
    fixed = preds["rules, real centres and scales"] == y_te
    best_learned = max(models, key=lambda k: acc(preds[k], y_te))
    out["best_learned"] = best_learned
    out["mcnemar"] = {
        "real centres vs shipped": mcnemar(base, preds["rules, real centres"] == y_te),
        "real centres and scales vs shipped": mcnemar(base, fixed),
        "%s vs shipped" % best_learned: mcnemar(base, preds[best_learned] == y_te),
        "%s vs recalibrated rules" % best_learned: mcnemar(
            fixed, preds[best_learned] == y_te),
    }
    print("\nMcNemar, paired on the same test faces")
    for k, v in out["mcnemar"].items():
        print("  %-42s p = %-10.3g %s" % (k, v["p_value"],
              "real difference" if v["significant_at_05"] else "cannot tell apart"))

    # ---- the app gates on frontal, so check that subset ------------------
    if fr_te.sum() > 30:
        out["frontal_only"] = {
            "n": int(fr_te.sum()),
            "share_of_test": round(float(fr_te.mean()), 3),
            "accuracy": {
                name: acc(p[fr_te], y_te[fr_te])
                for name, p in preds.items()
            },
        }
        print("\nfrontal faces only (%d of %d, the app rejects the rest)"
              % (fr_te.sum(), len(fr_te)))
        for name, a in sorted(out["frontal_only"]["accuracy"].items(),
                              key=lambda kv: -kv[1]):
            print("  %-36s %.3f" % (name, a))

    # ---- confusion, for the three that matter ----------------------------
    out["confusion"] = {"labels": CLASSES}
    for name in ("rules as shipped (5 shapes only)",
                 "rules, real centres and scales", best_learned):
        out["confusion"][name] = confusion_matrix(
            y_te, preds[name], labels=CLASSES).tolist()

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    print("\nwrote %s" % os.path.relpath(OUT, ROOT))


if __name__ == "__main__":
    main()
