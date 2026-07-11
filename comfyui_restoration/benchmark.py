"""Synthetic, redistributable benchmark fixtures and manifests."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path

from .media import tool_path


@dataclass(frozen=True)
class Fixture:
    name: str
    failure_modes: tuple[str, ...]
    duration_seconds: float
    license: str = "synthetic; generated from test signals"
    redistribution: str = "permitted"


FIXTURES = (
    Fixture("speech_click_hiss", ("speech", "click", "hiss"), 5.0),
    Fixture("music_speech", ("speech", "music", "stereo"), 5.0),
    Fixture("interlace_probe", ("interlaced", "motion"), 5.0),
)


def manifest() -> dict:
    return {"schema_version": "1", "corpus": "synthetic", "rights": "No external media; generated fixtures only", "fixtures": [asdict(fixture) for fixture in FIXTURES]}


def fixture_command(destination: Path, fixture: Fixture) -> list[str]:
    if fixture not in FIXTURES:
        raise ValueError("fixture is not in the pinned synthetic corpus")
    video_filter = "tinterlace=interleave_top" if "interlaced" in fixture.failure_modes else "null"
    video_rate = "50" if "interlaced" in fixture.failure_modes else "25"
    return [tool_path("ffmpeg"), "-hide_banner", "-y", "-f", "lavfi", "-i", f"testsrc=size=160x120:rate={video_rate}", "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000", "-t", str(fixture.duration_seconds), "-vf", video_filter, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "pcm_s16le", str(destination)]
