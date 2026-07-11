"""Safe media-tool adapters used by the workflow nodes.

All commands are lists, never shell fragments. The functions are intentionally small so a
ComfyUI host, a CLI, and a future MCP bridge can share exactly the same policy checks.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Sequence

from .core import MediaSource, workspace_path, write_json


def tool_path(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RuntimeError(f"required media tool is unavailable: {name}")
    return path


def run_command(args: Sequence[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    if not args or any("\x00" in value for value in args):
        raise ValueError("invalid empty or NUL-containing command")
    result = subprocess.run(tuple(args), cwd=cwd, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(f"command failed ({result.returncode}): {args[0]}\n{result.stderr[-2000:]}")
    return result


def ffprobe(source: Path) -> dict[str, Any]:
    result = run_command((tool_path("ffprobe"), "-hide_banner", "-v", "error", "-show_format", "-show_streams", "-show_chapters", "-of", "json", str(source)))
    return json.loads(result.stdout)


def ingest(path: Path, root: Path, *, streams: dict[str, int] | None = None) -> MediaSource:
    source = workspace_path(path, root)
    if source == root or source.is_dir() or source.name.startswith("restored"):
        raise ValueError("invalid or output-colliding source")
    probe = ffprobe(source)
    from .core import file_identity
    return MediaSource(str(source.relative_to(root)), file_identity(source), probe, streams or {})


def extract_audio(source: MediaSource, root: Path, output: Path, sample_rate: int = 48_000) -> list[str]:
    destination = workspace_path(output, root)
    if destination == workspace_path(Path(source.path), root):
        raise ValueError("refusing to overwrite source")
    destination.parent.mkdir(parents=True, exist_ok=True)
    return [tool_path("ffmpeg"), "-hide_banner", "-y", "-i", str(workspace_path(Path(source.path), root)), "-map", "0:a:0", "-c:a", "pcm_s24le", "-ar", str(sample_rate), "-ac", "2", str(destination)]


def write_probe(source: MediaSource, root: Path, destination: Path) -> None:
    write_json(workspace_path(destination, root), source.probe)
