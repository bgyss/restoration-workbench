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
from comfyui_restoration.audio import detect_clicks, repair_command


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
        detections = detect_clicks(audio, threshold=0.6)
        expected = list(fixture.expected_click_seconds)
        matched = sum(any(abs(event["timestamp"] - target) <= 0.01 for target in expected) for event in detections)
        click_eval = {"expected_seconds": expected, "detected_events": detections, "true_positives": matched, "false_positives": max(0, len(detections) - matched), "false_negatives": max(0, len(expected) - matched), "precision": matched / len(detections) if detections else 0.0, "recall": matched / len(expected) if expected else None}
        repair_eval = None
        if expected:
            repaired = output / f"{fixture.name}-repaired.wav"
            repair_args = repair_command(audio, repaired, method="adeclick")
            run_command(repair_args)
            repaired_events = detect_clicks(repaired, threshold=0.6)
            repair_eval = {"method": "adeclick", "command": repair_args, "before_click_events": len(detections), "after_click_events": len(repaired_events), "before_metrics": pcm_metrics(audio), "after_metrics": pcm_metrics(repaired), "repair_reduced_detected_events": len(repaired_events) < len(detections)}
        video = analysis["video"]
        entry = {"name": fixture.name, "failure_modes": fixture.failure_modes, "path": media.name, "sha256": sha256(media), "probe": probe, "audio_metrics": pcm_metrics(audio), "click_evaluation": click_eval, "repair_evaluation": repair_eval, "video_guardrails": {"width": video["width"], "height": video["height"], "frame_rate": video["frame_rate"], "interlaced_risk": analysis["interlaced_risk"], "faithful_lane_default": not analysis["interlaced_risk"]}, "candidate_matrix": "comfyui_restoration.candidates.audio_candidate_matrix"}
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
