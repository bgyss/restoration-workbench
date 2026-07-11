"""Typed, file-backed primitives shared by nodes and automation clients."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1"


def workspace_path(path: Path, root: Path) -> Path:
    """Return a resolved path inside *root*, rejecting symlink and traversal escapes."""
    root = root.resolve()
    candidate = path if path.is_absolute() else root / path
    resolved = candidate.resolve(strict=False)
    if not resolved.is_relative_to(root):
        raise ValueError(f"path is outside allowed workspace: {path}")
    if candidate.exists() and candidate.is_symlink():
        raise ValueError(f"symlink paths are not allowed: {path}")
    return resolved


def file_identity(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"media source is not a file: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    stat = path.stat()
    return {"sha256": digest.hexdigest(), "size": stat.st_size, "mtime_ns": stat.st_mtime_ns}


@dataclass(frozen=True)
class MediaSource:
    path: str
    identity: dict[str, Any]
    probe: dict[str, Any] = field(default_factory=dict)
    stream_selection: dict[str, int] = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION


@dataclass(frozen=True)
class SamplePlan:
    samples: tuple[dict[str, Any], ...]
    seed: int = 0
    rationale: str = "chapter and runtime coverage"
    schema_version: str = SCHEMA_VERSION


@dataclass(frozen=True)
class AudioArtifact:
    path: str
    sample_rate: int
    channels: int
    sample_count: int
    timeline_offset_ms: float = 0.0
    parents: tuple[str, ...] = ()
    schema_version: str = SCHEMA_VERSION


@dataclass(frozen=True)
class VideoArtifact:
    path: str
    width: int
    height: int
    frame_count: int
    frame_rate: str
    sar: str | None = None
    dar: str | None = None
    parents: tuple[str, ...] = ()
    schema_version: str = SCHEMA_VERSION


@dataclass(frozen=True)
class RestorationCandidate:
    branch: str
    parameters: dict[str, Any]
    output: str | None = None
    metrics: dict[str, Any] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()
    schema_version: str = SCHEMA_VERSION


@dataclass(frozen=True)
class ReviewBundle:
    path: str
    candidates: tuple[str, ...]
    approval_state: str = "pending"
    schema_version: str = SCHEMA_VERSION


@dataclass(frozen=True)
class RunManifest:
    run_id: str
    status: str
    root: str
    parents: tuple[str, ...] = ()
    commands: tuple[dict[str, Any], ...] = ()
    outputs: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    schema_version: str = SCHEMA_VERSION


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def write_manifest(path: Path, manifest: RunManifest) -> None:
    write_json(path, asdict(manifest))


def load_manifest(path: Path, *, root: Path | None = None) -> RunManifest:
    if root is not None and not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("manifest is outside the allowed workspace")
    data = json.loads(path.read_text())
    if data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported or stale manifest schema")
    required = {"run_id", "status", "root"}
    if not required <= data.keys() or data["status"] not in {"planned", "running", "cancelled", "complete", "failed"}:
        raise ValueError("malformed run manifest")
    return RunManifest(**data)
