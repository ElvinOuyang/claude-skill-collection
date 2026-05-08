#!/usr/bin/env python3
"""Generate @1x and @2x assets from an @3x source PNG.

Usage: scale_ios_assets.py <name>@3x.png <out-dir>

Writes <out-dir>/<name>@2x.png and <out-dir>/<name>@1x.png. Uses Lanczos
resampling because illustrations have soft edges where bilinear shows banding.

Critical correctness rule: the three scales must represent the SAME point
size. That means:
    size_1x  = source / 3
    size_2x  = (source / 3) * 2
    size_3x  = (source / 3) * 3 = source
For that arithmetic to land on integers, the source dimensions must be
divisible by 3. To also play nicely with @2x downstream consumers we want
divisibility by 6 (LCM of 2 and 3). If the source isn't a clean multiple, we
*pad* (transparent border) up to the next multiple of 6, since cropping
would clip subject content. The pad is centered so the subject stays in the
middle of the canvas. This guarantees the three scales are exact integer
point-equivalents, which the Asset Catalog relies on for crisp display.
"""
from __future__ import annotations

import argparse
import os
import sys

try:
    from PIL import Image
except ImportError:
    sys.stderr.write("Missing dependency. Install with: pip install pillow\n")
    sys.exit(2)


POINT_DIVISOR = 6  # LCM(2, 3); guarantees integer @1x, @2x, @3x sizes.


def _pad_to_multiple(img: Image.Image, multiple: int) -> Image.Image:
    """Center-pad the image with transparent pixels up to a multiple of `multiple`."""
    w, h = img.size
    new_w = ((w + multiple - 1) // multiple) * multiple
    new_h = ((h + multiple - 1) // multiple) * multiple
    if new_w == w and new_h == h:
        return img
    canvas = Image.new("RGBA", (new_w, new_h), (0, 0, 0, 0))
    canvas.paste(img, ((new_w - w) // 2, (new_h - h) // 2))
    return canvas


def scale(src_path: str, out_dir: str) -> None:
    base = os.path.basename(src_path)
    if "@3x" not in base:
        raise SystemExit(f"Source must contain '@3x' in filename: {base}")
    name_2x = base.replace("@3x", "@2x")
    name_1x = base.replace("@3x", "@1x")
    name_3x = base

    img = Image.open(src_path).convert("RGBA")
    w, h = img.size

    if w % POINT_DIVISOR != 0 or h % POINT_DIVISOR != 0:
        # Pad rather than fail. We tell the caller, since the @3x output also
        # needs to be re-saved at the padded size for the three scales to align.
        new_w = ((w + POINT_DIVISOR - 1) // POINT_DIVISOR) * POINT_DIVISOR
        new_h = ((h + POINT_DIVISOR - 1) // POINT_DIVISOR) * POINT_DIVISOR
        sys.stderr.write(
            f"Source {w}x{h} is not divisible by {POINT_DIVISOR}; "
            f"padding to {new_w}x{new_h} so @1x/@2x/@3x are exact integer "
            f"point-equivalents. Re-saving the padded source as @3x.\n"
        )
        img = _pad_to_multiple(img, POINT_DIVISOR)
        w, h = img.size
        # Overwrite/write the padded @3x so it stays consistent with @1x/@2x.
        img.save(os.path.join(out_dir, name_3x), format="PNG")

    # At this point w and h are guaranteed multiples of POINT_DIVISOR.
    point_w = w // 3
    point_h = h // 3
    size_1x = (point_w, point_h)
    size_2x = (point_w * 2, point_h * 2)

    img.resize(size_2x, Image.Resampling.LANCZOS).save(
        os.path.join(out_dir, name_2x), format="PNG"
    )
    img.resize(size_1x, Image.Resampling.LANCZOS).save(
        os.path.join(out_dir, name_1x), format="PNG"
    )


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source")
    p.add_argument("out_dir")
    args = p.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    scale(args.source, args.out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
