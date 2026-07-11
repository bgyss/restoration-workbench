"""Validation for the checked-in ComfyUI UI and API workflow formats."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REVIEW_REQUIRED = {"RestorationLoadMedia", "PlanRepresentativeSamples", "VideoBaselineRestore"}
FULL_REQUIRED = {"HumanApprovalGate", "ResumableFullRun"}
BUILTIN_UI_NODES = {"MarkdownNote"}


def _node_types(document: dict[str, Any]) -> set[str]:
    if isinstance(document.get("nodes"), list):
        return {str(node.get("type", "")) for node in document["nodes"]}
    return {
        str(node.get("class_type", ""))
        for node in document.values()
        if isinstance(node, dict) and "class_type" in node
    }


def validate_workflow(path: Path) -> set[str]:
    """Load one UI/API workflow and return its logical node types."""
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ValueError(f"{path}: workflow root must be an object")
    types = _node_types(document)
    if not types:
        raise ValueError(f"{path}: workflow has no nodes")
    if "full" in path.stem:
        required = FULL_REQUIRED
    else:
        required = REVIEW_REQUIRED
    missing = required - types
    if missing:
        raise ValueError(f"{path}: missing required node types: {', '.join(sorted(missing))}")
    return types


def validate_node_exports(document: dict[str, Any]) -> None:
    """Ensure logical workflow nodes are exported and API inputs cover required fields."""
    from .nodes import NODE_CLASS_MAPPINGS

    if isinstance(document.get("nodes"), list):
        types = _node_types(document)
        inputs_by_type = {str(node.get("type")): node.get("widgets_values", []) for node in document["nodes"]}
        del inputs_by_type
    else:
        for node in document.values():
            if not isinstance(node, dict) or "class_type" not in node:
                continue
            class_type = str(node["class_type"])
            if class_type not in NODE_CLASS_MAPPINGS:
                raise ValueError(f"workflow references unexported node: {class_type}")
            required = set(NODE_CLASS_MAPPINGS[class_type].INPUT_TYPES().get("required", {}))
            supplied = set(node.get("inputs", {}))
            missing = required - supplied
            if missing:
                raise ValueError(f"{class_type}: missing required inputs: {', '.join(sorted(missing))}")
        return
    missing = types - set(NODE_CLASS_MAPPINGS) - BUILTIN_UI_NODES
    if missing:
        raise ValueError(f"workflow references unexported node: {', '.join(sorted(missing))}")


def validate_workflows(directory: Path) -> dict[str, set[str]]:
    """Validate every checked-in workflow and return its node inventory."""
    paths = sorted(directory.glob("*.json"))
    if not paths:
        raise ValueError(f"{directory}: no workflow JSON files found")
    inventory: dict[str, set[str]] = {}
    for path in paths:
        document = json.loads(path.read_text(encoding="utf-8"))
        inventory[path.name] = validate_workflow(path)
        validate_node_exports(document)
    return inventory
