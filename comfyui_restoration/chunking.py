"""Deterministic chunk planners for bounded long-media processing."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable


@dataclass(frozen=True)
class AudioSegment:
    start_sample: int
    end_sample: int
    process: bool
    padded_start: int
    padded_end: int
    fade_samples: int


def route_audio(total_samples: int, speech_regions: Iterable[tuple[int, int]], *, padding_samples: int = 2_400, fade_samples: int = 2_400) -> list[AudioSegment]:
    if total_samples <= 0 or padding_samples < 0 or fade_samples < 0:
        raise ValueError("audio timeline and padding must be non-negative")
    regions = sorted((max(0, start), min(total_samples, end)) for start, end in speech_regions if start < end)
    result: list[AudioSegment] = []
    cursor = 0
    for start, end in regions:
        if cursor < start:
            result.append(AudioSegment(cursor, start, False, cursor, start, min(fade_samples, start - cursor)))
        result.append(AudioSegment(start, end, True, max(0, start - padding_samples), min(total_samples, end + padding_samples), min(fade_samples, end - start)))
        cursor = end
    if cursor < total_samples:
        result.append(AudioSegment(cursor, total_samples, False, cursor, total_samples, min(fade_samples, total_samples - cursor)))
    return result


def audio_route_manifest(total_samples: int, speech_regions: Iterable[tuple[int, int]], **kwargs) -> list[dict]:
    return [asdict(item) for item in route_audio(total_samples, speech_regions, **kwargs)]


@dataclass(frozen=True)
class VideoChunk:
    index: int
    start_frame: int
    end_frame: int
    process_start: int
    process_end: int
    overlap_frames: int


def plan_video_chunks(total_frames: int, *, chunk_frames: int = 150, overlap_frames: int = 12, scene_cuts: Iterable[int] = ()) -> list[VideoChunk]:
    if total_frames <= 0 or chunk_frames <= 0 or overlap_frames < 0 or overlap_frames >= chunk_frames:
        raise ValueError("invalid video chunk dimensions")
    cuts = sorted({cut for cut in scene_cuts if 0 < cut < total_frames})
    chunks: list[VideoChunk] = []
    start = 0
    index = 0
    while start < total_frames:
        target = min(total_frames, start + chunk_frames)
        nearby = [cut for cut in cuts if start < cut < target and cut - start >= chunk_frames // 3]
        end = nearby[-1] if nearby else target
        chunks.append(VideoChunk(index, start, end, max(0, start - overlap_frames), min(total_frames, end + overlap_frames), min(overlap_frames, end - start)))
        if end == total_frames:
            break
        start = end
        index += 1
    return chunks

