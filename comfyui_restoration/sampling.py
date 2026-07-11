"""Representative sample planning with explicit reasons and no source-specific assumptions."""

from __future__ import annotations

from typing import Iterable


def plan_samples(duration_seconds: float, *, chapters: Iterable[float] = (), defect_times: Iterable[float] = (), manual_times: Iterable[float] = (), sample_duration: float = 60.0) -> list[dict]:
    if duration_seconds <= 0 or sample_duration <= 0:
        raise ValueError("duration and sample duration must be positive")
    candidates: list[tuple[float, str, int]] = [(duration_seconds * fraction, reason, 0) for fraction, reason in ((0.01, "early runtime coverage"), (0.5, "middle runtime coverage"), (0.9, "late runtime coverage"))]
    candidates.extend((float(value), "chapter boundary", 1) for value in chapters)
    candidates.extend((float(value), "detected defect", 1) for value in defect_times)
    candidates.extend((float(value), "manual addition", 1) for value in manual_times)
    result: list[dict] = []
    seen: set[int] = set()
    half = sample_duration / 2
    for timestamp, reason, priority in sorted(candidates, key=lambda item: (item[0], item[2])):
        start = max(0.0, min(duration_seconds - sample_duration, timestamp - half))
        key = round(start * 1000)
        if key in seen:
            continue
        seen.add(key)
        result.append({"start": start, "duration": min(sample_duration, duration_seconds), "reason": reason})
    return result
