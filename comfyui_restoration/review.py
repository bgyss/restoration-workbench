"""Machine-readable review bundles; subjective approval remains human-owned."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .core import write_json


def build_review_bundle(root: Path, *, source: str, candidates: list[dict[str, Any]], detections: list[dict[str, Any]] | None = None) -> Path:
    bundle = root / "review" / "bundle.json"
    write_json(bundle, {"schema_version": "1", "source": source, "candidates": candidates, "detections": detections or [], "approval": {"status": "pending", "authority": "human"}})
    return bundle

