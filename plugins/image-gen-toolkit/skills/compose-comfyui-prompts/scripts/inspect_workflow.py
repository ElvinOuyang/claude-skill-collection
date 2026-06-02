#!/usr/bin/env python3
"""Inspect ComfyUI workflow JSON and match prompt requirements from a local catalog."""

from __future__ import annotations

import argparse
import fnmatch
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def infer_family(checkpoint: str) -> dict[str, str]:
    name = checkpoint.lower()
    if "pony" in name:
        return {"name": "pony-xl", "confidence": "heuristic"}
    if "illustrious" in name or "wai-" in name or "wai_" in name:
        return {"name": "illustrious-xl", "confidence": "heuristic"}
    if "sdxl" in name or "xl" in name:
        return {"name": "sdxl", "confidence": "heuristic"}
    return {"name": "unknown", "confidence": "unknown"}


def api_nodes(data: Any) -> list[dict[str, Any]]:
    if not isinstance(data, dict):
        return []
    nodes = []
    for node_id, node in data.items():
        if isinstance(node, dict) and "class_type" in node:
            nodes.append({
                "id": str(node_id),
                "type": str(node.get("class_type", "")),
                "inputs": node.get("inputs", {}),
            })
    return nodes


def ui_nodes(data: Any) -> list[dict[str, Any]]:
    raw_nodes = data.get("nodes", []) if isinstance(data, dict) else []
    nodes = []
    for node in raw_nodes:
        if not isinstance(node, dict):
            continue
        nodes.append({
            "id": str(node.get("id", "")),
            "type": str(node.get("type", "")),
            "widgets": node.get("widgets_values", []),
        })
    return nodes


def string_at(values: Any, index: int) -> str:
    if isinstance(values, list) and len(values) > index and isinstance(values[index], str):
        return values[index]
    return ""


def number_at(values: Any, index: int) -> float | None:
    if isinstance(values, list) and len(values) > index and isinstance(values[index], (int, float)):
        return float(values[index])
    return None


def extract(data: Any) -> dict[str, Any]:
    checkpoints: list[str] = []
    loras: list[dict[str, Any]] = []
    components: list[dict[str, str]] = []
    nodes = api_nodes(data)
    if nodes:
        for node in nodes:
            node_type = node["type"].lower()
            inputs = node["inputs"] if isinstance(node["inputs"], dict) else {}
            if "checkpointloader" in node_type:
                checkpoint = inputs.get("ckpt_name", "")
                if isinstance(checkpoint, str) and checkpoint:
                    checkpoints.append(checkpoint)
            if "lora" in node_type and "loader" in node_type:
                name = inputs.get("lora_name", "")
                if isinstance(name, str) and name:
                    loras.append({
                        "name": name,
                        "strength_model": inputs.get("strength_model"),
                        "strength_clip": inputs.get("strength_clip"),
                        "node_type": node["type"],
                    })
            for key, kind in (
                ("vae_name", "vae"),
                ("control_net_name", "controlnet"),
                ("embedding", "embedding"),
                ("style", "style"),
            ):
                value = inputs.get(key)
                if isinstance(value, str) and value:
                    components.append({"kind": kind, "name": value})
    else:
        for node in ui_nodes(data):
            node_type = node["type"].lower()
            widgets = node["widgets"]
            if "checkpointloader" in node_type:
                checkpoint = string_at(widgets, 0)
                if checkpoint:
                    checkpoints.append(checkpoint)
            if "lora" in node_type and "loader" in node_type:
                name = string_at(widgets, 0)
                if name:
                    loras.append({
                        "name": name,
                        "strength_model": number_at(widgets, 1),
                        "strength_clip": number_at(widgets, 2),
                        "node_type": node["type"],
                    })
    return {"checkpoints": checkpoints, "loras": loras, "other_components": components}


def matches(name: str, patterns: list[str]) -> bool:
    lowered = name.lower()
    for pattern in patterns:
        candidate = str(pattern).lower()
        if candidate in lowered or fnmatch.fnmatch(lowered, candidate):
            return True
    return False


def catalog_match(
    name: str,
    records: list[dict[str, Any]],
    kind: str | None = None,
) -> list[dict[str, Any]]:
    return [
        record
        for record in records
        if (kind is None or record.get("kind") == kind)
        and matches(name, record.get("match", []))
    ]


def collect_additions(
    records: list[dict[str, Any]],
    matched_additions: dict[str, list[Any]],
) -> None:
    for record in records:
        for key in matched_additions:
            matched_additions[key].extend(record.get(key, []))


def warn_above_recommended(
    lora: dict[str, Any],
    records: list[dict[str, Any]],
    warnings: list[str],
) -> None:
    for record in records:
        for strength_key in ("strength_model", "strength_clip"):
            loaded = lora.get(strength_key)
            recommended = record.get(f"recommended_{strength_key}")
            if (
                isinstance(loaded, (int, float))
                and isinstance(recommended, (int, float))
                and loaded > recommended
            ):
                warnings.append(
                    f"{lora['name']} {strength_key} is {loaded}; "
                    f"catalog recommends <= {recommended}"
                )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("workflow", type=Path)
    parser.add_argument("--catalog", type=Path)
    args = parser.parse_args()

    inventory = extract(load_json(args.workflow))
    checkpoint = inventory["checkpoints"][0] if inventory["checkpoints"] else ""
    records: list[dict[str, Any]] = []
    if args.catalog:
        catalog = load_json(args.catalog)
        records = catalog.get("components", []) if isinstance(catalog, dict) else []

    warnings: list[str] = []
    matched_additions = {"trigger_words": [], "positive_additions": [], "negative_additions": []}
    checkpoint_catalog_matches = catalog_match(checkpoint, records, "checkpoint")
    collect_additions(checkpoint_catalog_matches, matched_additions)

    for lora in inventory["loras"]:
        lora["catalog_matches"] = catalog_match(lora["name"], records, "lora")
        if not lora["catalog_matches"]:
            warnings.append(f"Add catalog metadata for active LoRA: {lora['name']}")
        collect_additions(lora["catalog_matches"], matched_additions)
        warn_above_recommended(lora, lora["catalog_matches"], warnings)

    for component in inventory["other_components"]:
        component["catalog_matches"] = catalog_match(
            component["name"], records, component["kind"]
        )
        if not component["catalog_matches"]:
            warnings.append(
                f"Add catalog metadata for active {component['kind']}: {component['name']}"
            )
        collect_additions(component["catalog_matches"], matched_additions)

    output = {
        "checkpoint": checkpoint,
        "all_checkpoints": inventory["checkpoints"],
        "checkpoint_catalog_matches": checkpoint_catalog_matches,
        "inferred_model_family": infer_family(checkpoint),
        "active_loras": inventory["loras"],
        "other_components": inventory["other_components"],
        "matched_prompt_additions": matched_additions,
        "warnings": warnings,
    }
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
