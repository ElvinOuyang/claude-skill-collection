#!/usr/bin/env python3
"""
extract_ios_tokens.py — scan an iOS / SwiftUI codebase for design-token signals
and emit a JSON dump grouped by category.

Output shape:

    {
      "platform": "ios",
      "root": "<path>",
      "colors":     [{ "value": "#2563EB",  "role_hint": "primary?", "sites": ["..."] }, ...],
      "typography": [{ "family": "SF Pro",  "size": 17, "weight": "regular", "sites": ["..."] }, ...],
      "spacing":    [{ "value": 16, "unit": "pt", "context": "padding", "sites": ["..."] }, ...],
      "components": [{ "name": "PrimaryButton", "file": "...", "summary": "..." }, ...],
      "layout":     [{ "kind": "cornerRadius", "value": 12, "sites": ["..."] }, ...],
      "asset_catalog_colors": [{ "name": "AccentColor", "set_path": "..." }, ...]
    }

Usage:
    python extract_ios_tokens.py <path-to-ios-project-root>

The output is intentionally noisy (every site is listed) so the skill can
present evidence to the user and resolve inconsistencies. The skill author is
expected to bucket findings into the 6-section DESIGN.md schema after the
extractor runs — this script does not do that bucketing itself.
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

HEX_RE = re.compile(r"#([0-9A-Fa-f]{6})\b")
RGB_RE = re.compile(r"Color\(\s*red:\s*([\d.]+)\s*,\s*green:\s*([\d.]+)\s*,\s*blue:\s*([\d.]+)")
NAMED_COLOR_RE = re.compile(r"Color\(\s*\"([^\"]+)\"\s*\)")
COLOR_LITERAL_RE = re.compile(r"Color\.(\w+)")
FONT_SYSTEM_RE = re.compile(r"\.font\(\s*\.system\(\s*size:\s*(\d+(?:\.\d+)?)\s*(?:,\s*weight:\s*\.(\w+))?")
FONT_CUSTOM_RE = re.compile(r"\.font\(\s*\.custom\(\s*\"([^\"]+)\"\s*,\s*size:\s*(\d+(?:\.\d+)?)")
FONT_TEXTSTYLE_RE = re.compile(r"\.font\(\s*\.(\w+)\s*\)")
PADDING_NUM_RE = re.compile(r"\.padding\(\s*(\.\w+\s*,\s*)?(\d+(?:\.\d+)?)\s*\)")
SPACING_RE = re.compile(r"spacing:\s*(\d+(?:\.\d+)?)")
CORNER_RADIUS_RE = re.compile(r"\.cornerRadius\(\s*(\d+(?:\.\d+)?)")
FRAME_HEIGHT_RE = re.compile(r"\.frame\([^)]*height:\s*(\d+(?:\.\d+)?)")

COMPONENT_RE = re.compile(r"struct\s+(\w+)\s*:\s*View\b")

SKIP_DIRS = {".git", ".build", "DerivedData", "Pods", "node_modules", ".swiftpm", "build", ".xcodeproj"}


def rgb_to_hex(r: float, g: float, b: float) -> str:
    def _c(v: float) -> int:
        if v <= 1.0:
            return max(0, min(255, int(round(v * 255))))
        return max(0, min(255, int(round(v))))
    return "#{:02X}{:02X}{:02X}".format(_c(r), _c(g), _c(b))


def is_skip(path: Path) -> bool:
    parts = set(path.parts)
    if parts & SKIP_DIRS:
        return True
    for p in path.parts:
        if p.endswith(".xcodeproj") or p.endswith(".xcassets"):
            # We DO want to walk into xcassets for color sets, but skip xcodeproj internals.
            if p.endswith(".xcodeproj"):
                return True
    return False


def walk_swift_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.endswith(".xcodeproj")]
        for fn in filenames:
            if fn.endswith(".swift"):
                yield Path(dirpath) / fn


def walk_xcassets(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        # Look for *.colorset directories anywhere in the tree (skipping git).
        for d in dirnames:
            if d.endswith(".colorset"):
                yield Path(dirpath) / d


def scan_swift(file_path: Path, rel: str, buckets: dict[str, list[Any]]):
    try:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return

    for line_no, line in enumerate(text.splitlines(), start=1):
        site = f"{rel}:{line_no}"

        for m in HEX_RE.finditer(line):
            buckets["colors"].append({
                "value": "#" + m.group(1).upper(),
                "role_hint": _role_hint(line),
                "site": site,
            })

        for m in RGB_RE.finditer(line):
            try:
                hex_val = rgb_to_hex(float(m.group(1)), float(m.group(2)), float(m.group(3)))
                buckets["colors"].append({
                    "value": hex_val,
                    "role_hint": _role_hint(line),
                    "site": site,
                    "from": "Color(red:green:blue:)",
                })
            except ValueError:
                continue

        for m in NAMED_COLOR_RE.finditer(line):
            buckets["asset_catalog_colors_referenced"].append({
                "name": m.group(1),
                "site": site,
            })

        for m in COLOR_LITERAL_RE.finditer(line):
            literal = m.group(1)
            if literal not in {"clear", "white", "black", "primary", "secondary", "accentColor"}:
                # "primary" and "secondary" are SwiftUI semantic colors; flag for review
                buckets["semantic_colors"].append({
                    "name": literal,
                    "site": site,
                })

        for m in FONT_SYSTEM_RE.finditer(line):
            buckets["typography"].append({
                "family": "system",
                "size": float(m.group(1)),
                "weight": m.group(2) or "regular",
                "site": site,
            })

        for m in FONT_CUSTOM_RE.finditer(line):
            buckets["typography"].append({
                "family": m.group(1),
                "size": float(m.group(2)),
                "weight": "(unspecified)",
                "site": site,
            })

        for m in FONT_TEXTSTYLE_RE.finditer(line):
            style = m.group(1)
            if style in {
                "largeTitle", "title", "title2", "title3",
                "headline", "subheadline", "body", "callout",
                "footnote", "caption", "caption2",
            }:
                buckets["typography"].append({
                    "family": "system (Dynamic Type)",
                    "textStyle": style,
                    "site": site,
                })

        for m in PADDING_NUM_RE.finditer(line):
            buckets["spacing"].append({
                "value": float(m.group(2)),
                "unit": "pt",
                "context": "padding",
                "site": site,
            })

        for m in SPACING_RE.finditer(line):
            buckets["spacing"].append({
                "value": float(m.group(1)),
                "unit": "pt",
                "context": "stack spacing",
                "site": site,
            })

        for m in CORNER_RADIUS_RE.finditer(line):
            buckets["layout"].append({
                "kind": "cornerRadius",
                "value": float(m.group(1)),
                "site": site,
            })

        for m in FRAME_HEIGHT_RE.finditer(line):
            buckets["layout"].append({
                "kind": "frameHeight",
                "value": float(m.group(1)),
                "site": site,
            })

    for m in COMPONENT_RE.finditer(text):
        buckets["components"].append({
            "name": m.group(1),
            "file": rel,
        })


def _role_hint(line: str) -> str:
    lower = line.lower()
    for keyword in ("background", "primary", "destructive", "error", "success",
                    "accent", "border", "surface", "text", "warning", "muted"):
        if keyword in lower:
            return keyword
    return ""


def scan_colorset(colorset_dir: Path, root: Path) -> dict[str, Any] | None:
    contents_json = colorset_dir / "Contents.json"
    if not contents_json.exists():
        return None
    try:
        data = json.loads(contents_json.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    name = colorset_dir.name.removesuffix(".colorset")
    appearances = []
    for entry in data.get("colors", []):
        color = entry.get("color", {})
        components = color.get("components", {})
        appearances.append({
            "appearance": [a.get("value") for a in entry.get("appearances", [])] or ["any"],
            "components": components,
        })
    return {
        "name": name,
        "set_path": str(colorset_dir.relative_to(root)),
        "appearances": appearances,
    }


def consolidate(buckets: dict[str, list[Any]]) -> dict[str, Any]:
    """Group raw site-level findings into per-value frequency lists."""
    def group_by(items: list[dict], key: str) -> list[dict]:
        grouped: dict[Any, dict[str, Any]] = defaultdict(lambda: {"sites": [], "extras": []})
        for it in items:
            v = it.get(key)
            grouped[v]["value"] = v
            grouped[v]["sites"].append(it.get("site"))
            extras = {k: it[k] for k in it if k not in {"site", key}}
            if extras and extras not in grouped[v]["extras"]:
                grouped[v]["extras"].append(extras)
        return sorted(
            (
                {
                    key: g["value"],
                    "occurrences": len(g["sites"]),
                    "sites": g["sites"][:8],  # cap so output stays scannable
                    "extras": g["extras"][:5],
                }
                for g in grouped.values()
            ),
            key=lambda d: -d["occurrences"],
        )

    return {
        "colors": group_by(buckets["colors"], "value"),
        "typography": buckets["typography"],
        "spacing": group_by(buckets["spacing"], "value"),
        "layout": buckets["layout"],
        "components": buckets["components"],
        "semantic_colors": buckets["semantic_colors"],
        "asset_catalog_colors_referenced": buckets["asset_catalog_colors_referenced"],
    }


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: extract_ios_tokens.py <project-root>", file=sys.stderr)
        return 2
    root = Path(argv[1]).resolve()
    if not root.exists():
        print(f"path does not exist: {root}", file=sys.stderr)
        return 2

    buckets: dict[str, list[Any]] = {
        "colors": [],
        "typography": [],
        "spacing": [],
        "layout": [],
        "components": [],
        "semantic_colors": [],
        "asset_catalog_colors_referenced": [],
    }

    for swift_file in walk_swift_files(root):
        rel = str(swift_file.relative_to(root))
        scan_swift(swift_file, rel, buckets)

    asset_colors = []
    for cs in walk_xcassets(root):
        info = scan_colorset(cs, root)
        if info is not None:
            asset_colors.append(info)

    consolidated = consolidate(buckets)
    output = {
        "platform": "ios",
        "root": str(root),
        **consolidated,
        "asset_catalog_colors": asset_colors,
    }
    json.dump(output, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
