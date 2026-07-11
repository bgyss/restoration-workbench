#!/usr/bin/env python3
"""Validate checked-in UI/API workflows against the public node contract."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from comfyui_restoration.workflows import validate_workflows


if __name__ == "__main__":
    inventory = validate_workflows(Path("examples/workflows"))
    for name, node_types in inventory.items():
        print(f"{name}: {', '.join(sorted(node_types))}")
