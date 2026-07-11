"""Conservative audio analysis and repair command builders."""

from __future__ import annotations

import math
import wave
from pathlib import Path
from typing import Any

from .media import tool_path


def detect_clicks(path: Path, *, threshold: float = 0.85, max_events: int = 10_000) -> list[dict[str, Any]]:
    """Detect short full-scale discontinuities without changing the source WAV."""
    with wave.open(str(path), "rb") as stream:
        rate, channels, width = stream.getframerate(), stream.getnchannels(), stream.getsampwidth()
        if width not in (2, 3, 4):
            raise ValueError("only integer PCM WAV widths 16/24/32 are supported")
        raw = stream.readframes(stream.getnframes())
    scale = float(1 << (width * 8 - 1))
    frame_size = channels * width
    previous: list[float] | None = None
    events: list[dict[str, Any]] = []
    for index in range(0, len(raw) - frame_size + 1, frame_size):
        current = []
        for channel in range(channels):
            start = index + channel * width
            current.append(int.from_bytes(raw[start : start + width], "little", signed=True) / scale)
        if previous is not None:
            jump = max(abs(a - b) for a, b in zip(current, previous))
            if jump >= threshold and max(abs(value) for value in current) >= threshold:
                events.append({"sample": index // frame_size, "timestamp": index / frame_size / rate, "channel": "all", "confidence": min(1.0, jump / 2), "duration_samples": 1})
                if len(events) >= max_events:
                    break
        previous = current
    return events


def repair_command(source: Path, destination: Path, *, method: str = "adeclick") -> list[str]:
    if method not in {"adeclick", "bypass"}:
        raise ValueError("unsupported audio repair method")
    filters = [] if method == "bypass" else ["-af", "adeclick"]
    return [tool_path("ffmpeg"), "-hide_banner", "-y", "-i", str(source), *filters, "-c:a", "pcm_s24le", str(destination)]


def guard_loudness_command(source: Path, destination: Path, *, true_peak: float = -1.0) -> list[str]:
    if not math.isfinite(true_peak) or true_peak > 0:
        raise ValueError("true peak ceiling must be finite and <= 0 dBTP")
    return [tool_path("ffmpeg"), "-hide_banner", "-y", "-i", str(source), "-af", f"loudnorm=I=-23:TP={true_peak}:LRA=11", "-c:a", "pcm_s24le", str(destination)]

