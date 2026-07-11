"""Export reports without leaking machine-specific absolute paths."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def redact(value: Any, root: Path) -> Any:
    if isinstance(value, dict):
        return {key: redact(item, root) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item, root) for item in value]
    if isinstance(value, str):
        text = value.replace(str(root.resolve()), "<workspace>")
        return re.sub(r"/(?:Users|home)/[^/\s]+", "<redacted-user>", text)
    return value


def export_json(source: Path, destination: Path, root: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(redact(json.loads(source.read_text()), root), indent=2, sort_keys=True) + "\n")

