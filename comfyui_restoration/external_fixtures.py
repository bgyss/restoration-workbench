"""Record evidence for an explicitly authorized external fixture download."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .media import ffprobe


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def record_fixture(
    source: Path,
    destination: Path,
    *,
    source_id: str,
    source_url: str,
    rights_url: str,
    license_name: str,
    repository_root: Path,
    probe: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Write a redacted evidence record for a file already downloaded outside the repository."""
    source = source.expanduser().resolve()
    repository_root = repository_root.resolve()
    if not source.is_file():
        raise ValueError("fixture source must be an existing file")
    try:
        source.relative_to(repository_root)
    except ValueError:
        pass
    else:
        raise ValueError("fixture media must be stored outside the repository")
    if not source_id.strip() or not source_url.startswith("https://") or not rights_url.startswith("https://"):
        raise ValueError("source identity and HTTPS rights/source URLs are required")
    if not license_name.strip():
        raise ValueError("license is required")
    evidence = {
        "schema_version": "1",
        "source_id": source_id,
        "source_url": source_url,
        "rights_url": rights_url,
        "license": license_name,
        "filename": source.name,
        "sha256": _sha256(source),
        "probe": probe if probe is not None else ffprobe(source),
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    import json
    destination.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    return evidence
