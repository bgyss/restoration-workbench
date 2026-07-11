"""Deterministic storage and bounded-run preflight helpers."""

from __future__ import annotations

import shutil
from pathlib import Path


def estimate_storage_bytes(
    duration_seconds: float,
    *,
    source_bitrate_bits: int = 8_000_000,
    intermediate_multiplier: float = 2.5,
    reserve_bytes: int = 512 * 1024 * 1024,
) -> int:
    """Estimate source-equivalent intermediates plus a fixed safety reserve."""
    if duration_seconds <= 0 or source_bitrate_bits <= 0 or intermediate_multiplier < 1 or reserve_bytes < 0:
        raise ValueError("invalid storage-estimate parameters")
    return int(duration_seconds * source_bitrate_bits / 8 * intermediate_multiplier + reserve_bytes)


def resource_preflight(
    root: Path,
    *,
    estimated_bytes: int,
    min_free_bytes: int = 0,
    max_chunks: int = 10_000,
    chunk_count: int,
) -> dict[str, int | bool]:
    """Check free space and bounded chunk count before an expensive run."""
    if estimated_bytes < 0 or min_free_bytes < 0 or chunk_count < 1 or chunk_count > max_chunks:
        raise ValueError("run exceeds resource bounds")
    usage = shutil.disk_usage(root)
    required = estimated_bytes + min_free_bytes
    return {
        "available_bytes": usage.free,
        "estimated_bytes": estimated_bytes,
        "required_bytes": required,
        "chunk_count": chunk_count,
        "within_bounds": usage.free >= required,
    }
