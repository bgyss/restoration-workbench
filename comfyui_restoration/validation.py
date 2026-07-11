"""Structured preservation and timeline validation for final outputs."""

from __future__ import annotations

import re
from typing import Any

from .media import run_command, tool_path


def qc_command(path: str) -> list[str]:
    """Build a decode-time QC command for black, silence, freeze, and clipping signals."""
    return [
        tool_path("ffmpeg"), "-hide_banner", "-i", path,
        "-vf", "blackdetect=d=1,freezedetect=n=-60dB:d=2",
        "-af", "silencedetect=n=-60dB:d=1,astats=metadata=1:reset=1",
        "-f", "null", "-",
    ]


def parse_qc_log(log: str) -> dict[str, Any]:
    """Parse FFmpeg filter diagnostics into the input shape accepted by :func:`evaluate_qc`."""
    def durations(pattern: str) -> float:
        return sum(float(value) for value in re.findall(pattern, log))

    return {
        "black_seconds": durations(r"black_duration:\s*([0-9]+(?:\.[0-9]+)?)"),
        "silence_seconds": durations(r"silence_duration:\s*([0-9]+(?:\.[0-9]+)?)"),
        "freeze_events": len(re.findall(r"freeze_duration:\s*[0-9]", log)),
        "clipping_samples": sum(int(value) for value in re.findall(r"(?:Number of clipped samples|clipping_samples):\s*([0-9]+)", log, re.I)),
    }


def run_qc(path: str) -> dict[str, Any]:
    """Run the fixed local FFmpeg QC command and return parsed observations."""
    result = run_command(qc_command(path))
    return {"path": path, "observations": parse_qc_log(result.stderr), "raw_log": result.stderr}


def evaluate_qc(
    qc: dict[str, Any], *, max_black_seconds: float = 2.0, max_silence_seconds: float | None = None,
) -> dict[str, Any]:
    """Turn parsed decode-QC observations into structured, non-subjective failures."""
    failures: list[str] = []
    black = float(qc.get("black_seconds", 0) or 0)
    silence = float(qc.get("silence_seconds", 0) or 0)
    frozen = int(qc.get("freeze_events", 0) or 0)
    clipped = int(qc.get("clipping_samples", 0) or 0)
    if black > max_black_seconds:
        failures.append("excessive black frames")
    if max_silence_seconds is not None and silence > max_silence_seconds:
        failures.append("excessive silence")
    if frozen:
        failures.append("frozen frames detected")
    if clipped:
        failures.append("clipped audio detected")
    return {"valid": not failures, "failures": failures, "observations": {"black_seconds": black, "silence_seconds": silence, "freeze_events": frozen, "clipping_samples": clipped}}


def _stream(probe: dict[str, Any], codec_type: str) -> dict[str, Any] | None:
    return next((item for item in probe.get("streams", []) if item.get("codec_type") == codec_type), None)


def validate_invariants(
    source: dict[str, Any], output: dict[str, Any], *, duration_tolerance: float = 0.1,
    qc: dict[str, Any] | None = None, require_video: bool = True, require_audio: bool = True,
) -> dict[str, Any]:
    source_video, output_video = _stream(source, "video"), _stream(output, "video")
    source_audio, output_audio = _stream(source, "audio"), _stream(output, "audio")
    failures: list[str] = []
    if require_video and not output_video:
        failures.append("missing video stream")
    if require_audio and not output_audio:
        failures.append("missing audio stream")
    if source_video and output_video:
        for field in ("width", "height", "r_frame_rate"):
            if source_video.get(field) != output_video.get(field):
                failures.append(f"video {field} changed")
    if require_audio and source_audio and output_audio:
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
    qc_result = evaluate_qc(qc) if qc is not None else None
    if qc_result:
        failures.extend(qc_result["failures"])
    return {"valid": not failures, "failures": failures, "duration_drift_seconds": output_duration - source_duration, "source_duration": source_duration, "output_duration": output_duration, "source_chapter_count": len(source_chapters), "output_chapter_count": len(output_chapters), "qc": qc_result}
