"""Render photoreal hairstyle catalogue images on Cloudflare Workers AI.

Why this exists: the hand-drawn SVGs from ``generate_hair_assets.py`` read as
clip art next to a real product catalogue. These renders replace the four
reference views. The transparent ``overlay.svg`` is deliberately NOT touched,
because the 2D try-on anchors that shape to the user's face landmarks and a
photograph cannot do that job.

Model: ``@cf/black-forest-labs/flux-2-klein-4b``. Two things about it that are
not in the docs and were established by trying:

  * It takes a ``multipart/form-data`` request, not JSON. A JSON body is
    rejected with "required properties at '/' are 'multipart'".
  * It ignores an input image, so there is no way to edit one shared base head,
    and it ignores ``seed``, so runs are not reproducible.

Consistency therefore comes from the prompt alone: every style shares an
identical prefix and suffix describing the mannequin, the framing, the
lighting, the backdrop and the hair colour, and only the middle sentence
changes. In practice that holds the look together well enough to read as one
catalogue.

Cost: roughly 104 neurons per 1024x1024 render against a free allowance of
10,000 per day, so about 96 images a day at no charge.

Run from the repo root:
    python tools/generate_hair_renders.py --sample
    python tools/generate_hair_renders.py --all --angles front,left,right,back --live
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
KB_PATH = REPO_ROOT / "backend" / "app" / "knowledge" / "hairstyles.yaml"
ENV_PATH = REPO_ROOT / "backend" / ".env"
LIVE_DIR = REPO_ROOT / "frontend" / "public" / "assets" / "hair"
PREVIEW_DIR = REPO_ROOT / "tools" / "render_preview"

MODEL = "@cf/black-forest-labs/flux-2-klein-4b"
# Measured, not quoted. Cloudflare documents 26.05 neurons per output 512x512
# tile, which would put a 1024x1024 render at 104. Reality is about five times
# that: a run of 21 exhausted the daily 10,000 after 18 images, twice, on
# separate days. Roughly 18 renders per day is the honest planning figure.
# The allowance resets at 00:00 UTC.
NEURONS_PER_IMAGE = 555
DAILY_FREE_NEURONS = 10_000

ANGLES = ("front", "left", "right", "back")

# Everything outside the middle sentence is identical for every style and every
# angle. This is the only thing holding the set together, so it is deliberately
# specific about material, framing, lighting and backdrop.
PREFIX = (
    "Studio catalogue photograph of a matte light-grey mannequin styling head. "
)
def suffix(colour: str) -> str:
    return (
        " Plain seamless very light warm grey background, soft even studio lighting, "
        "head centred in frame, sharp focus, high detail. Realistic hair with visible "
        f"strands and texture, {colour}. Any fringe stops at or above "
        "the eyebrows and never covers the eyes. Only the hair is hair: the "
        "mannequin head itself stays smooth matte grey."
    )


DEFAULT_COLOUR = "natural mid-brown colour"

# A few styles are defined by a texture that mid-brown European hair cannot
# show. Forcing one colour across the whole catalogue was making these render
# as something else entirely.
RENDER_COLOUR = {
    "waves-360": "very dark near-black tightly coiled hair",
    "afro-taper": "dark brown tightly coiled hair",
}

# The knowledge base describes a style for a person choosing one. That is not
# always enough for an image model, which reads "a tidy crop with a fade" and
# produces something generic. These override the description for rendering
# only. The YAML is left alone because it drives the recommendations, and
# bending it to suit an image model would be the wrong trade.
RENDER_HINT = {
    "curtain-bangs-lob": (
        "shoulder-length hair parted down the exact centre so the forehead is "
        "fully exposed in the middle, with the front sections sweeping away to "
        "the left and right like open curtains, shortest at the cheekbone and "
        "blending into the length. The centre of the forehead is bare skin, and "
        "no hair crosses it"
    ),
    "slick-back-undercut": (
        "hair on top swept straight backwards away from the forehead, smooth and "
        "glossy with comb lines running front to back, no side parting at all, and "
        "very short faded sides"
    ),
    "waves-360": (
        "hair cut very short and close to the scalp, brushed into a 360 wave "
        "pattern: tight concentric ripples like water, curved ridges radiating "
        "outward from a point at the crown across the entire head, a spinning "
        "wave texture. Not slicked, not parted, not long"
    ),
    "textured-fringe": (
        "a short crop with the top brushed forward into a soft fringe that rests "
        "on the upper forehead, ends lightly textured rather than blunt, sides "
        "tapered short"
    ),
    "french-crop": (
        "a short crop with a blunt fringe cut straight across the upper forehead, "
        "well above the eyebrows, with tapered faded sides"
    ),
    "edgar-crop": (
        "a blunt fringe cut in a hard straight line high across the forehead, "
        "brushed forward, with sharply faded sides and a visible hard line"
    ),
    "wolf-cut": (
        "a shaggy layered cut, soft and choppy rather than spiked, with volume "
        "through the crown, wispy face-framing layers and longer tapered ends at "
        "the nape"
    ),
}

# The camera. Without this the model settles on a three-quarter view every time.
ANGLE_PROMPT = {
    "front": "Strict front view, facing the camera straight on, symmetrical. ",
    "left": "Strict left profile view, the head turned ninety degrees to show its left side. ",
    "right": "Strict right profile view, the head turned ninety degrees to show its right side. ",
    "back": "Viewed from directly behind, showing the back of the head and the nape of "
            "the neck. No face is visible. ",
}

# Two short masculine cuts, one feminine mid-length and one shaggy unisex: the
# widest spread the catalogue offers, and the four the landing page shows.
SAMPLE_IDS = ("buzz-skin-fade", "burst-fade", "curtain-bangs-lob", "wolf-cut")


def load_env() -> tuple[str, str]:
    account = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "")
    if account and token:
        return account, token
    if not ENV_PATH.exists():
        sys.exit(f"No {ENV_PATH} and no Cloudflare credentials in the environment.")
    for line in io.open(ENV_PATH, encoding="utf-8"):
        if "=" not in line or line.lstrip().startswith("#"):
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip()
        if key == "CLOUDFLARE_ACCOUNT_ID" and value:
            account = value
        elif key == "CLOUDFLARE_API_TOKEN" and value:
            token = value
    if not account or not token:
        sys.exit("CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN must be set in backend/.env")
    return account, token


def load_styles() -> dict[str, dict]:
    raw = yaml.safe_load(KB_PATH.read_text(encoding="utf-8"))
    return {s["id"]: s for s in raw["styles"]}


def build_prompt(style: dict, angle: str) -> str:
    described = RENDER_HINT.get(style["id"], style["description"])
    colour = RENDER_COLOUR.get(style["id"], DEFAULT_COLOUR)
    return (
        PREFIX
        + ANGLE_PROMPT[angle]
        + f"The head is wearing a {style['name']} hairstyle: {described}"
        + suffix(colour)
    )


def render(account: str, token: str, prompt: str, timeout: int = 240) -> bytes:
    """One image from Workers AI. Raises on anything that is not an image."""
    boundary = "----cutpoint" + uuid.uuid4().hex
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="prompt"\r\n\r\n{prompt}\r\n'
        f"--{boundary}--\r\n"
    ).encode()

    url = (f"https://api.cloudflare.com/client/v4/accounts/{account}"
           f"/ai/run/{MODEL}")
    req = urllib.request.Request(url, method="POST")
    req.add_header("Authorization", "Bearer " + token)
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    req.data = body

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload, ctype = resp.read(), resp.headers.get("Content-Type", "")
    except urllib.error.HTTPError as exc:
        detail = exc.read()[:300].decode(errors="ignore")
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc

    if ctype.startswith("image/"):
        return payload
    data = json.loads(payload)
    if not data.get("success", True):
        raise RuntimeError(json.dumps(data.get("errors"))[:300])
    encoded = data.get("result", {}).get("image")
    if not encoded:
        raise RuntimeError("response carried no image")
    return base64.b64decode(encoded)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--sample", action="store_true",
                       help=f"only {', '.join(SAMPLE_IDS)}")
    group.add_argument("--all", action="store_true", help="every style in the catalogue")
    group.add_argument("--styles", help="comma-separated style ids")
    ap.add_argument("--angles", default="front",
                    help="comma-separated: front,left,right,back (default: front)")
    ap.add_argument("--live", action="store_true",
                    help="write into frontend/public/assets/hair rather than the preview dir")
    ap.add_argument("--force", action="store_true", help="regenerate files that already exist")
    args = ap.parse_args()

    account, token = load_env()
    styles = load_styles()

    if args.sample:
        wanted = [s for s in SAMPLE_IDS if s in styles]
    elif args.all:
        wanted = list(styles)
    else:
        wanted = [s.strip() for s in args.styles.split(",") if s.strip()]
        unknown = [s for s in wanted if s not in styles]
        if unknown:
            sys.exit(f"Unknown style ids: {unknown}")

    angles = [a.strip() for a in args.angles.split(",") if a.strip()]
    bad = [a for a in angles if a not in ANGLES]
    if bad:
        sys.exit(f"Unknown angles: {bad}")

    out_root = LIVE_DIR if args.live else PREVIEW_DIR
    planned = len(wanted) * len(angles)
    neurons = planned * NEURONS_PER_IMAGE

    print(f"Model:   {MODEL}")
    print(f"Styles:  {len(wanted)}   Angles: {', '.join(angles)}")
    print(f"Output:  {out_root}")
    print(f"Planned: {planned} renders, about {neurons:,} neurons "
          f"of the {DAILY_FREE_NEURONS:,} free per day")
    if neurons > DAILY_FREE_NEURONS:
        print("  NOTE: this exceeds one day's free allowance. Anything over it either "
              "bills or fails, so consider splitting the run across days.")
    print()

    done = skipped = failed = 0
    for i, style_id in enumerate(wanted, 1):
        style = styles[style_id]
        for angle in angles:
            dest = out_root / style_id / f"{angle}.png"
            label = f"[{i}/{len(wanted)}] {style_id} {angle}"
            if dest.exists() and not args.force:
                print(f"{label}: exists, skipping")
                skipped += 1
                continue
            try:
                blob = render(account, token, build_prompt(style, angle))
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(blob)
                print(f"{label}: saved ({len(blob) // 1024} KB)")
                done += 1
            except Exception as exc:
                print(f"{label}: FAILED - {exc}")
                failed += 1
            # Gentle on the rate limit; the free tier is shared.
            time.sleep(1.0)

    print(f"\nGenerated {done}, skipped {skipped}, failed {failed}.")
    print(f"Used roughly {done * NEURONS_PER_IMAGE:,} neurons.")
    if not args.live:
        print(f"\nPreview only. Nothing in "
              f"{LIVE_DIR.relative_to(REPO_ROOT)} was touched.")


if __name__ == "__main__":
    main()
