#!/usr/bin/env python3
"""Generate and measure the small synthetic corpus; outputs belong in a work directory."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from comfyui_restoration.benchmark import FIXTURES, fixture_command, manifest
from comfyui_restoration.media import ffprobe, run_command, tool_path
from comfyui_restoration.metrics import pcm_metrics
from comfyui_restoration.analysis import analyze_probe


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(output: Path) -> Path:
    output.mkdir(parents=True, exist_ok=True)
    report = manifest()
    report["fixtures"] = []
    for fixture in FIXTURES:
        media = output / f"{fixture.name}.mkv"
        run_command(fixture_command(media, fixture))
        probe = ffprobe(media)
        audio = output / f"{fixture.name}.wav"
        run_command((tool_path("ffmpeg"), "-hide_banner", "-y", "-i", str(media), "-map", "0:a:0", "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2", str(audio)))
        analysis = analyze_probe(probe)
        video = analysis["video"]
        entry = {"name": fixture.name, "failure_modes": fixture.failure_modes, "path": media.name, "sha256": sha256(media), "probe": probe, "audio_metrics": pcm_metrics(audio), "video_guardrails": {"width": video["width"], "height": video["height"], "frame_rate": video["frame_rate"], "interlaced_risk": analysis["interlaced_risk"], "faithful_lane_default": not analysis["interlaced_risk"]}, "candidate_matrix": "comfyui_restoration.candidates.audio_candidate_matrix"}
        report["fixtures"].append(entry)
    report_path = output / "benchmark-report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report_path


def main() -> int:
    output = Path(sys.argv[1]) if len(sys.argv) == 2 else Path(tempfile.mkdtemp(prefix="restoration-benchmark-"))
    try:
        report_path = run(output)
        print(report_path)
        return 0
    finally:
        if len(sys.argv) != 2:
            shutil.rmtree(output, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
