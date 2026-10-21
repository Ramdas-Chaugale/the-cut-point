"""Can a trained model classify face shape better than the hand-written rules?

    python experiments/face_classifier_study.py

The shipped classifier is rule based: measure four ratios plus the jaw angle,
compare against seven prototype faces with hand-set weights, take the nearest.
This asks whether learning those boundaries from data does better.

What this can and cannot answer
-------------------------------
The faces are generated from the same seven prototype definitions the rule based
classifier uses, with noise. So the honest question is narrow:

    can a model learn better decision boundaries than the hand-set
    weights and scales in face_classifier.py?

It is NOT evidence about real photographs. Doing that needs a labelled dataset of
real faces, which this project does not have. That limit is stated in the results
file and in the README rather than left for a reader to work out.

Writes results/face_classifier_study.json
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))

from scipy.stats import chi2                                   # noqa: E402
from sklearn.dummy import DummyClassifier                      # noqa: E402
from sklearn.ensemble import RandomForestClassifier            # noqa: E402
from sklearn.linear_model import LogisticRegression            # noqa: E402
from sklearn.metrics import confusion_matrix, f1_score         # noqa: E402
from sklearn.neural_network import MLPClassifier               # noqa: E402
from sklearn.pipeline import make_pipeline                     # noqa: E402
from sklearn.preprocessing import StandardScaler               # noqa: E402

from app.services import face_classifier as fc                 # noqa: E402
from app.services.face_geometry import compute_features        # noqa: E402

SHAPES = list(fc.CANONICAL_FACES)
RESULTS = os.path.join(ROOT, "results")

# How far a generated face is allowed to drift from its prototype, as a
# fraction of each measurement. Large enough that faces land between shapes,
# which is where a classifier earns its keep.
JITTER = 0.10


def make_face(shape: str, rng: np.random.Generator,
              jitter: float = JITTER) -> fc.CanonicalFace:
    """One face sampled around a prototype."""
    base = fc.CANONICAL_FACES[shape]
    def j(v: float) -> float:
        return float(v * (1.0 + rng.normal(0.0, jitter)))
    return fc.CanonicalFace(
        face_length=j(base.face_length),
        cheek_width=j(base.cheek_width),
        jaw_width=j(base.jaw_width),
        forehead_width=j(base.forehead_width),
    )


def features_of(face: fc.CanonicalFace,
                landmark_noise: float = 0.0,
                rng: np.random.Generator | None = None) -> np.ndarray:
    """Feature vector for a face, optionally with jitter on the landmarks.

    landmark_noise is a fraction of image width, applied to every point, which
    is how detector error actually shows up.
    """
    lm = fc.build_face_landmarks(face)
    if landmark_noise > 0.0 and rng is not None:
        lm = [(x + rng.normal(0, landmark_noise),
               y + rng.normal(0, landmark_noise), z) for x, y, z in lm]
    feats = compute_features(lm, fc._IMAGE, fc._IMAGE)
    return np.array(fc._feature_vector(feats), dtype=float)


def build_dataset(n_per_shape: int, seed: int,
                  landmark_noise: float = 0.0) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    X, y = [], []
    for shape in SHAPES:
        for _ in range(n_per_shape):
            face = make_face(shape, rng)
            X.append(features_of(face, landmark_noise, rng))
            y.append(shape)
    return np.array(X), np.array(y)


def rules_predict(X: np.ndarray) -> np.ndarray:
    """The shipped rule based classifier, reading the same feature vectors."""
    out = []
    for fv in X:
        logits = {s: -0.5 * fc._weighted_sq_distance(tuple(fv), p)
                  for s, p in fc.PROTOTYPES.items()}
        out.append(max(logits, key=logits.get))
    return np.array(out)


def accuracy(pred: np.ndarray, true: np.ndarray) -> float:
    return float((pred == true).mean())


def main() -> None:
    os.makedirs(RESULTS, exist_ok=True)

    # Separate seeds, so the test set is faces the models have never seen.
    X_train, y_train = build_dataset(600, seed=1)
    X_val,   y_val   = build_dataset(200, seed=2)
    X_test,  y_test  = build_dataset(200, seed=3)
    print("train %d | val %d | test %d  (%d shapes)"
          % (len(X_train), len(X_val), len(X_test), len(SHAPES)))

    models = {
        "always most common": DummyClassifier(strategy="most_frequent"),
        "logistic regression": make_pipeline(
            StandardScaler(), LogisticRegression(max_iter=2000)),
        "random forest": RandomForestClassifier(
            n_estimators=300, random_state=0),
        "small MLP": make_pipeline(
            StandardScaler(),
            MLPClassifier(hidden_layer_sizes=(32, 16), max_iter=3000,
                          random_state=0)),
    }

    out: dict = {
        "note": ("Faces are generated from the same seven prototypes the rule "
                 "based classifier uses, with 10% jitter. This measures whether "
                 "learned boundaries beat hand-set weights on that distribution. "
                 "It is not evidence about real photographs."),
        "jitter": JITTER,
        "n_train": len(X_train), "n_val": len(X_val), "n_test": len(X_test),
        "shapes": SHAPES,
        "test": {},
    }

    # The baseline is the code that actually ships.
    rules_test = rules_predict(X_test)
    out["test"]["rules (shipped)"] = {
        "accuracy": accuracy(rules_test, y_test),
        "macro_f1": float(f1_score(y_test, rules_test, average="macro")),
        "trained": False,
    }

    for name, model in models.items():
        model.fit(X_train, y_train)
        val = accuracy(model.predict(X_val), y_val)
        pred = model.predict(X_test)
        out["test"][name] = {
            "accuracy": accuracy(pred, y_test),
            "macro_f1": float(f1_score(y_test, pred, average="macro")),
            "val_accuracy": val,
            "trained": True,
        }

    print("\n%-22s %9s %9s" % ("", "test acc", "macro F1"))
    print("-" * 42)
    for name, r in sorted(out["test"].items(), key=lambda kv: -kv[1]["accuracy"]):
        print("%-22s %9.3f %9.3f" % (name, r["accuracy"], r["macro_f1"]))

    # Is the gap real, or could it be noise? Both predict on the SAME test
    # faces, so the comparison is paired and McNemar's test is the right one.
    best_name = max((k for k in out["test"] if out["test"][k]["trained"]
                     and k != "always most common"),
                    key=lambda k: out["test"][k]["accuracy"])
    best_pred = models[best_name].predict(X_test)
    rules_ok = rules_test == y_test
    learn_ok = best_pred == y_test
    b = int((rules_ok & ~learn_ok).sum())   # rules right, model wrong
    c = int((~rules_ok & learn_ok).sum())   # model right, rules wrong
    stat = (abs(b - c) - 1) ** 2 / (b + c) if (b + c) else 0.0
    p_value = float(chi2.sf(stat, 1))
    out["mcnemar"] = {
        "comparison": "%s vs rules (shipped)" % best_name,
        "rules_right_model_wrong": b,
        "model_right_rules_wrong": c,
        "statistic": float(stat),
        "p_value": p_value,
        "significant_at_05": p_value < 0.05,
    }
    print()
    print("McNemar, %s against the shipped rules" % best_name)
    print("  rules right, model wrong : %d" % b)
    print("  model right, rules wrong : %d" % c)
    print("  p = %.4g  ->  %s" % (p_value,
          "a real difference" if p_value < 0.05 else "cannot tell them apart"))

    # Which shapes get confused, for the best learned model and for the rules.
    best = best_name
    out["best_learned"] = best
    for label, pred in (("rules (shipped)", rules_test),
                        (best, models[best].predict(X_test))):
        cm = confusion_matrix(y_test, pred, labels=SHAPES)
        out.setdefault("confusion", {})[label] = cm.tolist()

    # Does the advantage survive landmark error? This is the question that
    # matters for a detector that is never pixel perfect.
    sweep = []
    for noise in (0.0, 0.002, 0.005, 0.01, 0.02, 0.03):
        Xn, yn = build_dataset(200, seed=4, landmark_noise=noise)
        row = {"noise": noise,
               "rules": accuracy(rules_predict(Xn), yn)}
        for name, model in models.items():
            if name == "always most common":
                continue
            row[name] = accuracy(model.predict(Xn), yn)
        sweep.append(row)
    out["noise_sweep"] = sweep

    print("\nlandmark noise, as a fraction of image width")
    keys = [k for k in sweep[0] if k != "noise"]
    print("%-8s %s" % ("noise", " ".join("%-20s" % k for k in keys)))
    for row in sweep:
        print("%-8.3f %s" % (row["noise"],
                             " ".join("%-20.3f" % row[k] for k in keys)))

    path = os.path.join(RESULTS, "face_classifier_study.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    print("\nwrote %s" % os.path.relpath(path, ROOT))


if __name__ == "__main__":
    main()
