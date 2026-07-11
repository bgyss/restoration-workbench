"""Explicit video candidate catalog used by sample planning and agent inspection."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class VideoCandidate:
    id: str
    lane: str
    kind: str
    repository: str
    license_note: str
    available: bool = False
    default: bool = False
    requires_temporal_qc: bool = True


VIDEO_CANDIDATES = (
    VideoCandidate("ffmpeg-faithful-baseline", "faithful", "deterministic", "https://ffmpeg.org/", "FFmpeg system-package license applies", True, True),
    VideoCandidate("opencv-multiframe-nlmeans", "faithful", "deterministic", "https://opencv.org/", "Apache-2.0; optional external adapter"),
    VideoCandidate("basicvsr-plus-plus", "experimental_reconstruction", "temporally_aware_neural", "https://github.com/ckkelvinchan/BasicVSR_PlusPlus", "Repository and weight terms require review"),
    VideoCandidate("rvrt", "experimental_reconstruction", "temporally_aware_neural", "https://github.com/JingyunLiang/RVRT", "CC-BY-NC repository components; not bundled"),
)


def candidate_catalog() -> list[dict[str, object]]:
    return [asdict(candidate) for candidate in VIDEO_CANDIDATES]


def candidate_by_id(candidate_id: str) -> VideoCandidate:
    for candidate in VIDEO_CANDIDATES:
        if candidate.id == candidate_id:
            return candidate
    raise KeyError(f"unknown video candidate: {candidate_id}")
