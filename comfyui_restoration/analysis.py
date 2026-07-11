"""Source analysis derived from FFprobe metadata without altering media."""

from __future__ import annotations

from typing import Any


def _ratio(value: str | None) -> float | None:
    if not value or ":" not in value:
        return None
    left, right = value.split(":", 1)
    try:
        return float(left) / float(right)
    except ValueError:
        return None


def analyze_probe(probe: dict[str, Any]) -> dict[str, Any]:
    streams = probe.get("streams", [])
    video = next((item for item in streams if item.get("codec_type") == "video"), {})
    audio = next((item for item in streams if item.get("codec_type") == "audio"), {})
    field_order = video.get("field_order")
    width, height = video.get("width"), video.get("height")
    geometric_ratio = width / height if width and height else None
    display_ratio = _ratio(video.get("display_aspect_ratio"))
    return {
        "duration_seconds": float(probe.get("format", {}).get("duration", 0) or 0),
        "chapter_count": len(probe.get("chapters", [])),
        "video": {"width": video.get("width"), "height": video.get("height"), "frame_rate": video.get("r_frame_rate"), "field_order": field_order, "sar": video.get("sample_aspect_ratio"), "dar": video.get("display_aspect_ratio"), "color_range": video.get("color_range"), "color_space": video.get("color_space"), "color_transfer": video.get("color_transfer"), "color_primaries": video.get("color_primaries")},
        "audio": {"sample_rate": audio.get("sample_rate"), "channels": audio.get("channels"), "channel_layout": audio.get("channel_layout"), "codec": audio.get("codec_name"), "start_time": audio.get("start_time")},
        "interlaced_risk": field_order not in (None, "progressive", "unknown"),
        "aspect_ratio": {"geometric": geometric_ratio, "display": display_ratio, "is_approximately_4_3": display_ratio is not None and abs(display_ratio - (4 / 3)) < 0.005, "metadata_matches_geometry": display_ratio is None or geometric_ratio is None or abs(display_ratio - geometric_ratio) < 0.005},
        "black_bar_analysis": "requires sample frames",
        "loudness_analysis": "requires decoded audio",
        "noise_profile": "requires representative sample",
        "defect_analysis": "requires decoded audio/video samples",
    }
