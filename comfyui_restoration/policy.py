"""Policy checks shared by node and agent-facing surfaces."""

from __future__ import annotations

from pathlib import Path

from .core import workspace_path


def output_path(root: Path, source: Path, requested: Path) -> Path:
    source = workspace_path(source, root)
    destination = workspace_path(requested, root)
    if destination == source:
        raise ValueError("output must not overwrite immutable source")
    if destination.is_relative_to(source.parent) and destination.name == source.name:
        raise ValueError("output/source collision refused")
    return destination


def validate_sample_window(start: float, duration: float, source_duration: float) -> None:
    if start < 0 or duration <= 0 or start + duration > source_duration + 1e-6:
        raise ValueError("sample window is outside source duration")

