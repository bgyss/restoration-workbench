"""Deterministic, dependency-free PCM guardrail metrics."""

from __future__ import annotations

import math
import wave
from pathlib import Path


def pcm_metrics(path: Path) -> dict[str, float | int]:
    with wave.open(str(path), "rb") as stream:
        channels, width, frames = stream.getnchannels(), stream.getsampwidth(), stream.getnframes()
        if width not in (2, 3, 4):
            raise ValueError("unsupported PCM width")
        raw = stream.readframes(frames)
    scale = float(1 << (width * 8 - 1))
    values = [int.from_bytes(raw[index : index + width], "little", signed=True) / scale for index in range(0, len(raw), width)]
    if not values:
        raise ValueError("empty audio")
    rms = math.sqrt(sum(value * value for value in values) / len(values))
    peak = max(abs(value) for value in values)
    dc = sum(values) / len(values)
    return {"channels": channels, "sample_count": frames, "rms": rms, "peak": peak, "integrated_dbfs_estimate": 20 * math.log10(max(rms, 1e-12)), "dc_offset": dc, "clipping_samples": sum(abs(value) >= 0.999 for value in values)}

