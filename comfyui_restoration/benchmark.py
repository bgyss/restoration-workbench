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
    expected_click_seconds: tuple[float, ...] = ()


FIXTURES = (
    Fixture("speech_click_hiss", ("speech", "click", "hiss"), 5.0, expected_click_seconds=(1.0,)),
    Fixture("music_speech", ("speech", "music", "stereo"), 5.0),
    Fixture("interlace_probe", ("interlaced", "motion"), 5.0),
)


def manifest() -> dict:
    fixtures = []
    for fixture in FIXTURES:
        record = asdict(fixture)
        record["failure_modes"] = list(fixture.failure_modes)
        record["expected_click_seconds"] = list(fixture.expected_click_seconds)
        fixtures.append(record)
    return {"schema_version": "1", "corpus": "synthetic", "rights": "No external media; generated fixtures only", "fixtures": fixtures}


def fixture_command(destination: Path, fixture: Fixture) -> list[str]:
    if fixture not in FIXTURES:
        raise ValueError("fixture is not in the pinned synthetic corpus")
    video_filter = "tinterlace=interleave_top" if "interlaced" in fixture.failure_modes else "null"
    video_rate = "50" if "interlaced" in fixture.failure_modes else "25"
    audio = "sine=frequency=440:sample_rate=48000"
    if fixture.name == "speech_click_hiss":
        audio = r"aevalsrc=exprs=0.2*sin(2*PI*440*t)+if(between(t\,1\,1.001)\,0.9\,0):s=48000[tone];anoisesrc=color=white:amplitude=0.01:sample_rate=48000[hiss];[tone][hiss]amix=inputs=2:duration=longest:normalize=0"
    elif fixture.name == "music_speech":
        audio = "sine=frequency=440:sample_rate=48000[speech];sine=frequency=660:sample_rate=48000[music];[speech][music]amix=inputs=2:duration=longest"
    return [tool_path("ffmpeg"), "-hide_banner", "-y", "-f", "lavfi", "-i", f"testsrc=size=160x120:rate={video_rate}", "-f", "lavfi", "-i", audio, "-t", str(fixture.duration_seconds), "-vf", video_filter, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "pcm_s16le", "-ac", "2", str(destination)]
