#!/usr/bin/env python3
"""Chroma-key magenta (#FF00FF) out of a PNG, producing a transparent PNG.

Usage: strip_magenta.py <input.png> <output.png> [--threshold 40] [--feather 8]

The threshold controls how close to pure magenta a pixel must be to become
transparent. The feather widens the alpha falloff at the subject edge so
anti-aliased pixels don't leave a magenta halo.
"""
from __future__ import annotations

import argparse
import sys

try:
    from PIL import Image
    import numpy as np
except ImportError:
    sys.stderr.write(
        "Missing dependency. Install with: pip install pillow numpy\n"
    )
    sys.exit(2)


def strip_magenta(in_path: str, out_path: str, threshold: int, feather: int) -> None:
    img = Image.open(in_path).convert("RGBA")
    arr = np.array(img)

    r, g, b, a = arr[..., 0], arr[..., 1], arr[..., 2], arr[..., 3]

    # Distance from pure magenta in RGB. Magenta = (255, 0, 255).
    dr = 255 - r.astype(np.int16)
    dg = g.astype(np.int16)
    db = 255 - b.astype(np.int16)
    dist = np.sqrt(dr * dr + dg * dg + db * db)

    # Hard alpha: anything within `threshold` of pure magenta becomes transparent.
    new_alpha = np.where(dist < threshold, 0, 255).astype(np.uint8)

    # Feathered falloff at the subject boundary to kill the magenta halo on
    # anti-aliased edges. A simple linear ramp over `feather` units of distance
    # past the threshold.
    if feather > 0:
        ramp_zone = (dist >= threshold) & (dist < threshold + feather)
        ramp = ((dist[ramp_zone] - threshold) / feather) * 255
        new_alpha[ramp_zone] = ramp.astype(np.uint8)

    out = np.dstack([r, g, b, np.minimum(new_alpha, a)]).astype(np.uint8)
    Image.fromarray(out, mode="RGBA").save(out_path, format="PNG")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--threshold", type=int, default=40)
    p.add_argument("--feather", type=int, default=8)
    args = p.parse_args()
    strip_magenta(args.input, args.output, args.threshold, args.feather)
    return 0


if __name__ == "__main__":
    sys.exit(main())
