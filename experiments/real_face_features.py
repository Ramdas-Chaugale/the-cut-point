"""Measure real photographs with the same geometry the app uses.

    python experiments/real_face_features.py --per-class 300

Downloads a labelled face-shape dataset, runs MediaPipe FaceLandmarker over each
image, and feeds the landmarks through the project's own compute_features. Writes
the resulting numbers to results/real_face_features.csv.

Why only numbers are saved
--------------------------
The images are photographs of real people, re-hosted by a third party. Measurements
derived from a photo are not the photo, so the five ratios get committed and the
images do not. They are cached under .cache/ , which is git-ignored, and can be
deleted at any time. Re-running this script rebuilds them.

The images are the input to the measurement, not a redistributable part of this
project. Anyone reproducing the study downloads them for themselves by running this.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import cv2
import mediapipe as mp
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))

from app.services import face_classifier as fc                 # noqa: E402
from app.services.face_geometry import compute_features        # noqa: E402

# Five labelled shapes. The app knows seven; diamond and triangle have no
# labelled examples here, which the study reports rather than works around.
CLASSES = ["heart", "oblong", "oval", "round", "square"]

DATASET = "codernotme/face_shape"
MODEL_URL = ("https://storage.googleapis.com/mediapipe-models/face_landmarker/"
             "face_landmarker/float16/1/face_landmarker.task")

CACHE = os.path.join(ROOT, ".cache")
IMAGES = os.path.join(CACHE, "face_shape_images")
MODEL = os.path.join(CACHE, "face_landmarker.task")
OUT = os.path.join(ROOT, "results", "real_face_features.csv")

COLUMNS = ["label", "image", "width", "height",
           "length_to_width", "forehead_to_cheek", "jaw_to_cheek",
           "forehead_to_jaw", "jaw_angle_deg", "is_frontal"]


def fetch_model() -> str:
    if not os.path.exists(MODEL):
        os.makedirs(CACHE, exist_ok=True)
        print("fetching the MediaPipe face landmarker model")
        urllib.request.urlretrieve(MODEL_URL, MODEL)
    return MODEL


def dataset_listing() -> dict[str, list[str]]:
    """Per-class file lists, straight from the dataset index."""
    url = "https://huggingface.co/api/datasets/" + DATASET
    meta = json.load(urllib.request.urlopen(url, timeout=60))
    files = [s["rfilename"] for s in meta.get("siblings", [])]
    return {c: sorted(f for f in files if f.startswith(c + "/")) for c in CLASSES}


def local_path(rel: str) -> str:
    return os.path.join(IMAGES, rel.replace("/", os.sep))


def download(rel: str) -> str | None:
    dest = local_path(rel)
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return dest
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    url = "https://huggingface.co/datasets/%s/resolve/main/%s" % (
        DATASET, urllib.parse.quote(rel))
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "the-cut-point"})
        data = urllib.request.urlopen(req, timeout=120).read()
    except Exception:
        return None
    if not data:
        return None
    with open(dest, "wb") as f:
        f.write(data)
    return dest


def make_landmarker():
    from mediapipe.tasks import python as mpp
    from mediapipe.tasks.python import vision
    opts = vision.FaceLandmarkerOptions(
        base_options=mpp.BaseOptions(model_asset_path=fetch_model()),
        running_mode=vision.RunningMode.IMAGE,
        num_faces=1)
    return vision.FaceLandmarker.create_from_options(opts)


def measure(path: str, landmarker) -> tuple | None:
    """One row of numbers for one image, or None if it cannot be measured."""
    img = cv2.imread(path)
    if img is None:
        return None
    h, w = img.shape[:2]
    rgb = np.ascontiguousarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    res = landmarker.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb))
    if not res.face_landmarks:
        return None
    lm = [(p.x, p.y, p.z) for p in res.face_landmarks[0]]
    try:
        f = compute_features(lm, w, h)
    except ValueError:
        return None
    return (w, h, f.length_to_width, f.forehead_to_cheek, f.jaw_to_cheek,
            f.forehead_to_jaw, f.jaw_angle_deg, f.is_frontal)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-class", type=int, default=300,
                    help="images to measure per shape")
    ap.add_argument("--workers", type=int, default=16,
                    help="parallel downloads")
    args = ap.parse_args()

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    os.makedirs(IMAGES, exist_ok=True)

    listing = dataset_listing()
    for c in CLASSES:
        if not listing[c]:
            raise SystemExit("no files listed for class %r" % c)

    wanted = {c: listing[c][:args.per_class] for c in CLASSES}
    total = sum(len(v) for v in wanted.values())
    print("dataset %s" % DATASET)
    print("classes %s" % ", ".join(CLASSES))
    print("asking for %d images per class, %d in total" % (args.per_class, total))

    # Downloads are IO bound, so run them wide. Measurement is CPU bound and
    # the landmarker is not thread safe, so that part stays sequential.
    print("downloading")
    flat = [(c, rel) for c in CLASSES for rel in wanted[c]]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        paths = list(pool.map(lambda t: download(t[1]), flat))

    missing = sum(1 for p in paths if p is None)
    if missing:
        print("  %d could not be downloaded" % missing)

    print("measuring")
    landmarker = make_landmarker()
    rows, no_face, unreadable = [], 0, 0
    done = 0
    for (label, rel), path in zip(flat, paths):
        if path is None:
            unreadable += 1
            continue
        m = measure(path, landmarker)
        done += 1
        if done % 200 == 0:
            print("  %d / %d" % (done, total))
        if m is None:
            no_face += 1
            continue
        rows.append([label, rel] + list(m))

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(COLUMNS)
        wr.writerows(rows)

    print()
    print("measured %d of %d images" % (len(rows), total))
    print("  no face found : %d" % no_face)
    print("  unreadable    : %d" % unreadable)
    per = {}
    frontal = 0
    for r in rows:
        per[r[0]] = per.get(r[0], 0) + 1
        if r[-1]:
            frontal += 1
    print("  per class     : %s" % ", ".join("%s %d" % (k, per[k])
                                             for k in CLASSES))
    print("  frontal       : %d (%.0f%%)" % (frontal, 100 * frontal / max(len(rows), 1)))
    print()
    print("wrote %s" % os.path.relpath(OUT, ROOT))
    print("images cached under .cache/ and not committed")


if __name__ == "__main__":
    main()
