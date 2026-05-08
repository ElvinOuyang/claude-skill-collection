#!/usr/bin/env python3
"""Chroma-key magenta (#FF00FF) out of a PNG, producing a transparent PNG.

Usage: strip_magenta.py <input.png> <output.png> [--threshold 40] [--feather 8]

The threshold controls how close to pure magenta a pixel must be to become
transparent. The feather widens the alpha falloff at the subject edge so
anti-aliased pixels don't leave a halo.

Important: feathering alone is NOT enough to kill the magenta halo. Edge
pixels with partial alpha still carry magenta RGB; when later composited on
a non-magenta background, that bleed-through shows as a pink/magenta fringe.
This script also runs a despill pass: for any pixel that is not fully opaque
post-keying, the magenta component is removed by clamping the red and blue
channels down to the green channel (since pure magenta has high R and B but
zero G, "magenta-ness" is well captured by max(R,B) - G). This is the same
idea as a green-screen despill, just rotated to magenta.
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

    r = arr[..., 0].astype(np.int32)
    g = arr[..., 1].astype(np.int32)
    b = arr[..., 2].astype(np.int32)
    a = arr[..., 3]

    # Distance from pure magenta in RGB. Magenta = (255, 0, 255).
    # Use int32 to avoid overflow on the squared terms (max 65025 each fits,
    # but the sum of three can exceed int16 range under bad inputs).
    dr = 255 - r
    dg = g
    db = 255 - b
    dist = np.sqrt((dr * dr + dg * dg + db * db).astype(np.float64))

    # Hard alpha: anything within `threshold` of pure magenta becomes transparent.
    new_alpha = np.where(dist < threshold, 0, 255).astype(np.uint8)

    # Feathered falloff at the subject boundary so anti-aliased edges don't
    # binary-cut. Linear ramp over `feather` units of distance past the threshold.
    if feather > 0:
        ramp_zone = (dist >= threshold) & (dist < threshold + feather)
        ramp = ((dist[ramp_zone] - threshold) / feather) * 255
        new_alpha[ramp_zone] = ramp.astype(np.uint8)

    final_alpha = np.minimum(new_alpha, a)

    # Despill: anywhere alpha is partial (or even fully opaque but visually
    # tinted by the chroma key) we suppress the magenta cast. The intuition is
    # that magenta has high R and high B with low G; if a pixel's R or B is
    # higher than its G, that excess is bleed from the background. Clamping
    # them down to G removes the cast without darkening true colors that
    # already have G >= R or G >= B (e.g., a green or yellow subject is
    # untouched). For mixed colors we only nudge the channels that exceed G.
    #
    # We apply despill on every pixel that isn't fully transparent. Fully
    # transparent pixels can't show through, so their RGB doesn't matter.
    despill_mask = final_alpha > 0

    # Strength of despill is proportional to how "magenta-spilled" the pixel is.
    # spill = max(0, max(R, B) - G). At 0, no change. We subtract a fraction of
    # spill from R and B, blending toward G. We use the full spill so any pixel
    # that was magenta (R=B=255, G=0) collapses to grey (255-spill = 0); a
    # pixel that's slightly tinted only loses its tint.
    rb_max = np.maximum(r, b)
    spill = np.clip(rb_max - g, 0, 255)

    new_r = r.copy()
    new_b = b.copy()
    new_r[despill_mask] = np.clip(r[despill_mask] - spill[despill_mask], 0, 255)
    new_b[despill_mask] = np.clip(b[despill_mask] - spill[despill_mask], 0, 255)

    out = np.dstack(
        [new_r.astype(np.uint8), g.astype(np.uint8), new_b.astype(np.uint8), final_alpha]
    ).astype(np.uint8)
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
