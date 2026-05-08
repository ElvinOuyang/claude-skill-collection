#!/usr/bin/env python3
"""
extract_web_tokens.py — scan a web codebase for design-token signals and emit
a JSON dump in the same shape as extract_ios_tokens.py.

Sources scanned:

- tailwind.config.{js,cjs,mjs,ts}: theme.extend.colors / fontFamily / spacing /
  borderRadius (parsed structurally where possible, regex fallback otherwise).
- CSS files: custom properties (`--color-*`, `--space-*`, `--radius-*`, etc.),
  hex literals, font-family declarations, px/rem/em values.
- design-tokens.json / tokens.json / tokens.css if present.
- Any *.tsx / *.jsx file: hex literals, inline tailwind class strings (top-level
  scan for noise; the user picks canonical values).

Usage:
    python extract_web_tokens.py <path-to-web-project-root>
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

HEX_RE = re.compile(r"#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})\b")
CSS_VAR_DECL_RE = re.compile(r"(--[a-zA-Z0-9_-]+)\s*:\s*([^;]+);")
CSS_FONT_FAMILY_RE = re.compile(r"font-family\s*:\s*([^;]+);", re.IGNORECASE)
CSS_PX_RE = re.compile(r"(\d+(?:\.\d+)?)px")
CSS_REM_RE = re.compile(r"(\d+(?:\.\d+)?)rem")
CSS_RADIUS_RE = re.compile(r"border-radius\s*:\s*([^;]+);", re.IGNORECASE)
CSS_PADDING_RE = re.compile(r"padding\s*:\s*([^;]+);", re.IGNORECASE)

TAILWIND_CONFIG_NAMES = {"tailwind.config.js", "tailwind.config.cjs",
                        "tailwind.config.mjs", "tailwind.config.ts"}
TOKEN_FILE_NAMES = {"design-tokens.json", "tokens.json", "tokens.css", "design-tokens.css"}

SKIP_DIRS = {".git", "node_modules", "dist", "build", ".next", ".nuxt",
             "out", "coverage", ".turbo", ".svelte-kit", "__pycache__"}


def is_skip_dir(d: str) -> bool:
    return d in SKIP_DIRS or d.startswith(".")


def walk(root: Path, exts: set[str]):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not is_skip_dir(d)]
        for fn in filenames:
            if Path(fn).suffix.lower() in exts:
                yield Path(dirpath) / fn
            elif fn in TOKEN_FILE_NAMES:
                yield Path(dirpath) / fn


def find_tailwind_configs(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not is_skip_dir(d)]
        for fn in filenames:
            if fn in TAILWIND_CONFIG_NAMES:
                yield Path(dirpath) / fn


def scan_tailwind(file_path: Path, rel: str) -> dict[str, Any]:
    """Best-effort regex parse of tailwind.config to surface theme.extend tokens.
    A real JS parser would be more robust; this is intentionally minimal so the
    skill stays runtime-light. The skill is expected to read the file too if the
    extraction is incomplete."""
    text = file_path.read_text(encoding="utf-8", errors="ignore")
    out: dict[str, Any] = {"file": rel, "raw_excerpt": ""}

    extend_match = re.search(r"extend\s*:\s*\{(.+?)\n\s*\}\s*,?\s*\}", text, re.DOTALL)
    if extend_match:
        out["raw_excerpt"] = extend_match.group(1)[:2000]

    out["colors"] = re.findall(
        r"['\"]([\w-]+)['\"]\s*:\s*['\"](#[0-9A-Fa-f]{3,8})['\"]", text
    )
    out["fontFamilies"] = re.findall(
        r"fontFamily\s*:\s*\{([^}]+)\}", text, re.DOTALL
    )
    out["spacing_keys"] = re.findall(
        r"spacing\s*:\s*\{([^}]+)\}", text, re.DOTALL
    )
    return out


def scan_css(file_path: Path, rel: str, buckets: dict[str, list[Any]]):
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

        for m in CSS_VAR_DECL_RE.finditer(line):
            buckets["css_vars"].append({
                "name": m.group(1),
                "value": m.group(2).strip(),
                "site": site,
            })

        for m in CSS_FONT_FAMILY_RE.finditer(line):
            buckets["typography"].append({
                "family": m.group(1).strip(),
                "site": site,
                "from": "css.font-family",
            })

        for m in CSS_PX_RE.finditer(line):
            buckets["spacing"].append({
                "value": float(m.group(1)),
                "unit": "px",
                "site": site,
            })

        for m in CSS_REM_RE.finditer(line):
            buckets["spacing"].append({
                "value": float(m.group(1)),
                "unit": "rem",
                "site": site,
            })

        for m in CSS_RADIUS_RE.finditer(line):
            buckets["layout"].append({
                "kind": "border-radius",
                "value": m.group(1).strip(),
                "site": site,
            })


def scan_jsx_or_tsx(file_path: Path, rel: str, buckets: dict[str, list[Any]]):
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


def _role_hint(line: str) -> str:
    lower = line.lower()
    for keyword in ("background", "primary", "destructive", "error", "success",
                    "accent", "border", "surface", "text", "warning", "muted",
                    "danger", "info"):
        if keyword in lower:
            return keyword
    return ""


def consolidate(buckets: dict[str, list[Any]]) -> dict[str, Any]:
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
                    "sites": g["sites"][:8],
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
        "css_vars": buckets["css_vars"],
    }


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: extract_web_tokens.py <project-root>", file=sys.stderr)
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
        "css_vars": [],
    }

    tailwind_configs = []
    for tw in find_tailwind_configs(root):
        rel = str(tw.relative_to(root))
        tailwind_configs.append(scan_tailwind(tw, rel))

    for css_file in walk(root, {".css", ".scss", ".sass", ".less"}):
        rel = str(css_file.relative_to(root))
        scan_css(css_file, rel, buckets)

    for tsx_file in walk(root, {".tsx", ".jsx", ".ts", ".js", ".vue", ".svelte"}):
        rel = str(tsx_file.relative_to(root))
        scan_jsx_or_tsx(tsx_file, rel, buckets)

    consolidated = consolidate(buckets)
    output = {
        "platform": "web",
        "root": str(root),
        **consolidated,
        "tailwind_configs": tailwind_configs,
    }
    json.dump(output, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
