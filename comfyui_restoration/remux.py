"""Preservation-aware remux and validation command construction."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from .media import tool_path


def remux_command(source: Path, video: Path, audio: Path, destination: Path, *, delay_ms: int = 0) -> list[str]:
    """Build a stream-copy remux command while retaining source metadata/chapters."""
    if destination in {source, video, audio}:
        raise ValueError("remux destination must be distinct from all inputs")
    if shutil.which("mkvmerge"):
        # The source is a metadata-only first input: mkvmerge carries its chapters/tags while
        # the approved filtered video and audio are selected from the following inputs.
        return [tool_path("mkvmerge"), "-o", str(destination), "--no-video", "--no-audio", str(source), str(video), "--sync", f"0:{delay_ms}", str(audio)]
    return [tool_path("ffmpeg"), "-hide_banner", "-y", "-i", str(video), "-itsoffset", str(delay_ms / 1000), "-i", str(audio), "-i", str(source), "-map", "0:v:0", "-map", "1:a:0", "-map_metadata", "2", "-map_chapters", "2", "-c", "copy", "-avoid_negative_ts", "disabled", str(destination)]


def validation_command(path: Path) -> list[str]:
    return [tool_path("ffmpeg"), "-hide_banner", "-v", "error", "-i", str(path), "-f", "null", "-"]


def compare_streams(source_probe: dict[str, Any], output_probe: dict[str, Any]) -> dict[str, Any]:
    """Return preservation facts without treating aesthetic metrics as automatic truth."""
    def streams(probe: dict) -> list[dict]:
        return [item for item in probe.get("streams", []) if item.get("codec_type") in {"video", "audio"}]
    before, after = streams(source_probe), streams(output_probe)
    return {"source_stream_count": len(before), "output_stream_count": len(after), "stream_count_preserved": len(before) == len(after), "source_duration": source_probe.get("format", {}).get("duration"), "output_duration": output_probe.get("format", {}).get("duration")}
