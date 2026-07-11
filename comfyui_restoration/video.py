"""Faithful video lane: explicit, cadence-preserving FFmpeg commands."""

from __future__ import annotations

from pathlib import Path

from .media import tool_path
from .chunking import VideoChunk


def _distinct(source: Path, destination: Path) -> None:
    if source.resolve() == destination.resolve():
        raise ValueError("video destination must not overwrite source")


def ensure_progressive(probe: dict) -> None:
    video = next((item for item in probe.get("streams", []) if item.get("codec_type") == "video"), None)
    if video and video.get("field_order") not in (None, "progressive", "unknown"):
        raise ValueError("source may be interlaced; faithful lane refuses implicit deinterlacing")


def deinterlace_command(
    source: Path,
    destination: Path,
    *,
    field_order: str,
    mode: str = "send_frame",
) -> list[str]:
    """Build an explicit interlace branch; cadence changes must be visible in the graph."""
    _distinct(source, destination)
    if field_order in ("", "progressive", "unknown"):
        raise ValueError("deinterlace branch requires a detected interlaced field order")
    if mode not in {"send_frame", "send_field"}:
        raise ValueError("unsupported deinterlace mode")
    return [
        tool_path("ffmpeg"), "-hide_banner", "-y", "-i", str(source),
        "-vf", f"yadif=mode={mode}:parity=auto:deint=interlaced",
        "-map", "0:v:0", "-c:v", "libx264", "-crf", "19", "-preset", "slow",
        "-pix_fmt", "yuv420p", "-an", str(destination),
    ]


def baseline_command(source: Path, destination: Path, *, crf: int = 19, target_aspect: str = "preserve") -> list[str]:
    _distinct(source, destination)
    if not 16 <= crf <= 24:
        raise ValueError("conservative CRF must be between 16 and 24")
    crop = {"preserve": None, "4:3": "crop=iw:iw*3/4", "16:9": "crop=iw:iw*9/16", "1:1": "crop=ih:ih"}
    if target_aspect not in crop:
        raise ValueError("unsupported target aspect ratio")
    filters = ["pp7=qp=2:mode=medium", "hqdn3d=3:2:6:4"]
    if crop[target_aspect]:
        filters.append(crop[target_aspect])
    return [tool_path("ffmpeg"), "-hide_banner", "-y", "-i", str(source), "-vf", ",".join(filters), "-map", "0:v:0", "-c:v", "libx264", "-crf", str(crf), "-preset", "slow", "-pix_fmt", "yuv420p", "-an", str(destination)]


def experimental_model_request(model: str, source: Path, destination: Path, *, strength: float = 0.1, seed: int = 0) -> dict:
    if not model.strip() or not 0 <= strength <= 1:
        raise ValueError("model and strength are required")
    return {"lane": "experimental_reconstruction", "model": model, "source": str(source), "destination": str(destination), "strength": strength, "seed": seed, "warning": "generated detail is not recovered historical fact"}


def stitch_qc(chunks: list[VideoChunk], *, expected_frames: int) -> dict:
    if not chunks or chunks[0].start_frame != 0 or chunks[-1].end_frame != expected_frames:
        raise ValueError("chunk plan does not cover the complete timeline")
    gaps = [right.start_frame - left.end_frame for left, right in zip(chunks, chunks[1:])]
    return {"expected_frames": expected_frames, "chunk_count": len(chunks), "timeline_covered": not any(gap != 0 for gap in gaps), "overlap_frames": [chunk.overlap_frames for chunk in chunks], "seam_checks": [{"left": left.index, "right": right.index, "status": "pending_human_qc"} for left, right in zip(chunks, chunks[1:])]}
