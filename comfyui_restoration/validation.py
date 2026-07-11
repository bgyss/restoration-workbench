"""Structured preservation and timeline validation for final outputs."""

from __future__ import annotations

from typing import Any


def _stream(probe: dict[str, Any], codec_type: str) -> dict[str, Any] | None:
    return next((item for item in probe.get("streams", []) if item.get("codec_type") == codec_type), None)


def validate_invariants(source: dict[str, Any], output: dict[str, Any], *, duration_tolerance: float = 0.1) -> dict[str, Any]:
    source_video, output_video = _stream(source, "video"), _stream(output, "video")
    source_audio, output_audio = _stream(source, "audio"), _stream(output, "audio")
    failures: list[str] = []
    if not output_video:
        failures.append("missing video stream")
    if not output_audio:
        failures.append("missing audio stream")
    if source_video and output_video:
        for field in ("width", "height", "r_frame_rate"):
            if source_video.get(field) != output_video.get(field):
                failures.append(f"video {field} changed")
    if source_audio and output_audio:
        for field in ("sample_rate", "channels"):
            if source_audio.get(field) != output_audio.get(field):
                failures.append(f"audio {field} changed")
        source_start = source_audio.get("start_time")
        output_start = output_audio.get("start_time")
        if source_start is not None and output_start is not None and abs(float(source_start) - float(output_start)) > duration_tolerance:
            failures.append("audio timeline offset changed")
    source_chapters, output_chapters = source.get("chapters", []), output.get("chapters", [])
    if source_chapters and len(source_chapters) != len(output_chapters):
        failures.append("chapter count changed")
    source_duration = float(source.get("format", {}).get("duration", 0) or 0)
    output_duration = float(output.get("format", {}).get("duration", 0) or 0)
    if source_duration and output_duration and abs(source_duration - output_duration) > duration_tolerance:
        failures.append("duration drift exceeds tolerance")
    return {"valid": not failures, "failures": failures, "duration_drift_seconds": output_duration - source_duration, "source_duration": source_duration, "output_duration": output_duration, "source_chapter_count": len(source_chapters), "output_chapter_count": len(output_chapters)}
