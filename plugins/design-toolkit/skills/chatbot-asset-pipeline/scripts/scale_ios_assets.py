#!/usr/bin/env python3
"""Generate @1x and @2x assets from an @3x source PNG.

Usage: scale_ios_assets.py <name>@3x.png <out-dir>

Writes <out-dir>/<name>@2x.png and <out-dir>/<name>@1x.png. Uses Lanczos
resampling because illustrations have soft edges where bilinear shows banding.
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


def scale(src_path: str, out_dir: str) -> None:
    base = os.path.basename(src_path)
    if "@3x" not in base:
        raise SystemExit(f"Source must contain '@3x' in filename: {base}")
    name_2x = base.replace("@3x", "@2x")
    name_1x = base.replace("@3x", "@1x")

    img = Image.open(src_path).convert("RGBA")
    w, h = img.size
    img.resize((w * 2 // 3, h * 2 // 3), Image.Resampling.LANCZOS).save(
        os.path.join(out_dir, name_2x), format="PNG"
    )
    img.resize((w // 3, h // 3), Image.Resampling.LANCZOS).save(
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
