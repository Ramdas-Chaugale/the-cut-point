"""Move reviewed renders from the preview folder into the live assets.

The raw renders are 1024x1024 PNGs of about half a megabyte each. The app
shows them in cards around 180px wide and in a detail view around 400px, so
shipping the originals would mean roughly 40MB of assets to serve a few
hundred kilobytes of actual visual information.

So each one is resized and written as WebP, which is what every browser the
app targets supports. The originals stay in the preview folder, so a different
size or format is a re-run of this script rather than a re-render.

The transparent `overlay.svg` in each style folder is left untouched: the 2D
try-on anchors that vector shape to the user's face landmarks, and a
photograph cannot do that job.

    python tools/promote_renders.py --dry-run
    python tools/promote_renders.py
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
PREVIEW = REPO_ROOT / "tools" / "render_preview"
LIVE = REPO_ROOT / "frontend" / "public" / "assets" / "hair"

ANGLES = ("front", "left", "right", "back")
SIZE = 512
QUALITY = 82


def human(n: int) -> str:
    return f"{n / 1e6:.1f} MB" if n >= 1e6 else f"{n / 1e3:.0f} KB"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="report without writing")
    ap.add_argument("--size", type=int, default=SIZE, help=f"square px (default {SIZE})")
    ap.add_argument("--quality", type=int, default=QUALITY, help=f"WebP quality (default {QUALITY})")
    ap.add_argument("--keep-svg", action="store_true",
                    help="leave the old angle SVGs in place instead of deleting them")
    args = ap.parse_args()

    if not PREVIEW.exists():
        raise SystemExit(f"No preview folder at {PREVIEW}. Run generate_hair_renders.py first.")

    src_bytes = out_bytes = 0
    written = missing = removed = 0

    for style_dir in sorted(p for p in PREVIEW.iterdir() if p.is_dir()):
        style_id = style_dir.name
        for angle in ANGLES:
            src = style_dir / f"{angle}.png"
            if not src.exists():
                missing += 1
                continue

            dest_dir = LIVE / style_id
            dest = dest_dir / f"{angle}.webp"
            img = Image.open(src).convert("RGB")
            img = img.resize((args.size, args.size), Image.LANCZOS)

            src_bytes += src.stat().st_size
            if args.dry_run:
                # Measure what it would cost without touching the tree.
                import io as _io
                buf = _io.BytesIO()
                img.save(buf, "WEBP", quality=args.quality, method=6)
                out_bytes += buf.tell()
            else:
                dest_dir.mkdir(parents=True, exist_ok=True)
                img.save(dest, "WEBP", quality=args.quality, method=6)
                out_bytes += dest.stat().st_size
                # The angle SVGs are superseded. overlay.svg is not.
                old = dest_dir / f"{angle}.svg"
                if old.exists() and not args.keep_svg:
                    old.unlink()
                    removed += 1
            written += 1

    verb = "would write" if args.dry_run else "wrote"
    print(f"{verb} {written} webp files at {args.size}px, quality {args.quality}")
    if missing:
        print(f"  {missing} angle(s) not rendered yet, skipped")
    if removed:
        print(f"  removed {removed} superseded angle SVGs (overlay.svg kept)")
    print(f"  source PNGs: {human(src_bytes)}")
    print(f"  output webp: {human(out_bytes)}")
    if src_bytes:
        print(f"  saving:      {100 * (1 - out_bytes / src_bytes):.0f}%")

    if not args.dry_run:
        kept = sorted(p.name for p in LIVE.glob("*/overlay.svg"))
        print(f"  overlay.svg still present in {len(kept)} style folders")


if __name__ == "__main__":
    main()
