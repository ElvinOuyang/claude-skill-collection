#!/usr/bin/env python3
"""
sample_pixel.py — Sample one pixel (or the mean of a small box) from a screenshot.

Usage:
  sample_pixel.py <image.png> <x> <y>
  sample_pixel.py <image.png> <x> <y> --box <size>

Coordinates are in image pixels (i.e. the same coordinate space as the PNG).
If you have logical points from `axe describe-ui`, multiply by the simulator's
display scale (typically 2x or 3x) before calling this script.

Output is a single line of JSON:
  {"x": 100, "y": 200, "rgba": [45, 140, 255, 255], "hex": "#2D8CFF"}

This is a deliberately simple helper. It samples one pixel (or a small mean box)
and that is all. It is not OCR, layer extraction, or alpha-aware compositing.
For gradients, blurs, or translucent overlays, the result is meaningless — flag
those findings as "manual visual verification needed" instead.

Requires Pillow (`pip install pillow`).
"""

from __future__ import annotations

import argparse
import json
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Sample a pixel from a PNG.")
    parser.add_argument("image", help="Path to the screenshot PNG.")
    parser.add_argument("x", type=int, help="X coordinate (image pixels).")
    parser.add_argument("y", type=int, help="Y coordinate (image pixels).")
    parser.add_argument(
        "--box",
        type=int,
        default=1,
        help="Average over a box of this size centered on (x,y). Default 1 = single pixel.",
    )
    args = parser.parse_args()

    try:
        from PIL import Image
    except ImportError:
        print(
            "ERROR: Pillow is required. Install with: pip install pillow",
            file=sys.stderr,
        )
        return 2

    img = Image.open(args.image).convert("RGBA")
    w, h = img.size
    if not (0 <= args.x < w and 0 <= args.y < h):
        print(
            f"ERROR: ({args.x},{args.y}) is outside image bounds {w}x{h}",
            file=sys.stderr,
        )
        return 2

    half = max(args.box // 2, 0)
    x0 = max(args.x - half, 0)
    y0 = max(args.y - half, 0)
    x1 = min(args.x + half + 1, w)
    y1 = min(args.y + half + 1, h)

    pixels = [img.getpixel((px, py)) for px in range(x0, x1) for py in range(y0, y1)]
    n = len(pixels)
    r = round(sum(p[0] for p in pixels) / n)
    g = round(sum(p[1] for p in pixels) / n)
    b = round(sum(p[2] for p in pixels) / n)
    a = round(sum(p[3] for p in pixels) / n)

    result = {
        "x": args.x,
        "y": args.y,
        "box": args.box,
        "rgba": [r, g, b, a],
        "hex": f"#{r:02X}{g:02X}{b:02X}",
    }
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
