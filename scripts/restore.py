#!/usr/bin/env python3
"""Conservative, sample-first VHS restoration runner."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

SAMPLES = {"A": 0, "B": 5940, "C": 10800}
BASELINE_TIMES = (90, 3600, 7200, 10800, 14400, 18000)


def quote(value: str) -> str:
    return "'" + value.replace("'", "'\\''") + "'"


@dataclass
class Runner:
    source: Path
    workdir: Path
    commands: list[str]

    def run(self, args: Sequence[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
        self.commands.append(" ".join(quote(a) for a in args))
        print("$ " + self.commands[-1])
        return subprocess.run(args, check=True, text=True, capture_output=capture)

    def ffmpeg(self, *args: str, capture: bool = False):
        return self.run(("ffmpeg", "-hide_banner", "-y", *args), capture=capture)

    def ffprobe(self, *args: str, capture: bool = False):
        return self.run(("ffprobe", "-hide_banner", *args), capture=capture)


def require_tools(names: Sequence[str]) -> None:
    missing = [name for name in names if shutil.which(name) is None]
    if missing:
        raise SystemExit("Missing required tools: " + ", ".join(missing))


def safe_workdir(source: Path, workdir: Path) -> None:
    source, workdir = source.resolve(), workdir.resolve()
    if source == workdir or source.parent == workdir:
        raise SystemExit("Refusing to use the source's directory as --workdir; use a copy directory.")
    workdir.mkdir(parents=True, exist_ok=True)
    for name in ("baseline", "samples", "review", "output"):
        (workdir / name).mkdir(exist_ok=True)


def probe(r: Runner) -> dict:
    result = r.ffprobe("-v", "error", "-show_format", "-show_streams", "-of", "json", str(r.source), capture=True)
    data = json.loads(result.stdout)
    (r.workdir / "baseline" / "source-ffprobe.json").write_text(json.dumps(data, indent=2) + "\n")
    return data


def duration(data: dict) -> float:
    return float(data.get("format", {}).get("duration", 0))


def validate_source(data: dict) -> None:
    streams = data.get("streams", [])
    video = next((stream for stream in streams if stream.get("codec_type") == "video"), None)
    audio = next((stream for stream in streams if stream.get("codec_type") == "audio"), None)
    problems = []
    if not video:
        problems.append("no video stream")
    else:
        if (video.get("width"), video.get("height")) != (720, 544):
            problems.append(f"video is {video.get('width')}x{video.get('height')}, expected 720x544")
        if video.get("field_order") not in (None, "progressive", "unknown"):
            problems.append(f"video field order is {video.get('field_order')}; inspect before proceeding")
        rate = video.get("r_frame_rate")
        if rate not in ("25/1", "25/0"):
            problems.append(f"video rate is {rate}, expected 25 fps")
    if not audio:
        problems.append("no audio stream")
    elif (audio.get("sample_rate"), audio.get("channels")) != ("48000", 2):
        problems.append("audio is not 48 kHz stereo")
    if problems:
        raise SystemExit("Source facts do not match restoration prompt: " + "; ".join(problems))


def phase_one(r: Runner, data: dict) -> None:
    r.ffmpeg("-i", str(r.source), "-map", "0:a:0", "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2", str(r.workdir / "audio_src.wav"))
    for i, timestamp in enumerate(BASELINE_TIMES, 1):
        r.ffmpeg("-ss", str(timestamp), "-i", str(r.source), "-frames:v", "1", "-vf", "format=rgb24", str(r.workdir / "baseline" / f"frame-{i:02d}.png"))
    for i, timestamp in enumerate((30, 900, 3600, 7200, 10800, 14400, 18000, max(0, duration(data) - 60)), 1):
        r.ffmpeg("-ss", str(timestamp), "-i", str(r.source), "-frames:v", "1", str(r.workdir / "baseline" / f"combing-check-{i:02d}.png"))
    loudness = r.ffmpeg("-i", str(r.workdir / "audio_src.wav"), "-af", "ebur128=framelog=verbose", "-f", "null", "-", capture=True)
    (r.workdir / "baseline" / "audio-ebur128.txt").write_text(loudness.stderr)
    stats = r.ffmpeg("-i", str(r.workdir / "audio_src.wav"), "-af", "astats=metadata=1:reset=1", "-f", "null", "-", capture=True)
    (r.workdir / "baseline" / "audio-astats.txt").write_text(stats.stderr)


def extract_samples(r: Runner) -> None:
    for label, start in SAMPLES.items():
        r.ffmpeg("-ss", str(start), "-i", str(r.source), "-t", "60", "-map", "0:v:0", "-map", "0:a:0?", "-c", "copy", str(r.workdir / "samples" / f"sample-{label}-source.mkv"))


def audio_restore(r: Runner, method: str) -> str:
    declicked = r.workdir / "audio_declicked.wav"
    r.ffmpeg("-i", str(r.workdir / "audio_src.wav"), "-af", "adeclick", str(declicked))
    chosen = method if method != "auto" else ("deepfilter" if shutil.which("deep-filter") else "sox")
    clean = r.workdir / "audio_clean.wav"
    if chosen == "deepfilter":
        outdir = r.workdir / "deepfilter"
        outdir.mkdir(exist_ok=True)
        r.run(("deep-filter", "--attenuation-limit", "6", str(declicked), "--output-dir", str(outdir)))
        candidates = sorted(outdir.glob("*.wav"))
        if not candidates:
            raise RuntimeError("deep-filter produced no WAV output")
        shutil.copyfile(candidates[0], clean)
    else:
        profile = r.workdir / "hiss-profile.noiseprof"
        r.run(("sox", str(declicked), "-n", "trim", "30", "1", "noiseprof", str(profile)))
        r.run(("sox", str(declicked), str(clean), "noisered", str(profile), "0.20"))
    r.ffmpeg("-i", str(clean), "-c:a", "aac", "-b:a", "192k", str(r.workdir / "audio_clean.m4a"))
    return chosen


def video_filter() -> str:
    return "pp7=qp=2:mode=medium,hqdn3d=3:2:6:4"


def video_samples(r: Runner) -> None:
    vf = video_filter()
    for label in SAMPLES:
        source = r.workdir / "samples" / f"sample-{label}-source.mkv"
        filtered = r.workdir / "samples" / f"sample-{label}-filtered.mkv"
        r.ffmpeg("-i", str(source), "-vf", vf, "-c:v", "libx264", "-crf", "19", "-preset", "slow", "-c:a", "copy", str(filtered))
        r.ffmpeg("-i", str(source), "-i", str(filtered), "-filter_complex", "[0:v][1:v]ssim=stats_file=" + str(r.workdir / "review" / f"ssim-{label}.log"), "-an", "-f", "null", "-")
        for index, timestamp in enumerate((10, 25, 40, 55), 1):
            for stem, media in (("source", source), ("filtered", filtered)):
                r.ffmpeg("-ss", str(timestamp), "-i", str(media), "-frames:v", "1", str(r.workdir / "review" / f"sample-{label}-{index:02d}-{stem}.png"))


def full_encode(r: Runner, source_duration: float) -> float:
    start = time.monotonic()
    out = r.workdir / "output" / "video_clean.mkv"
    r.ffmpeg("-i", str(r.source), "-map", "0:v:0", "-vf", video_filter(), "-c:v", "libx264", "-crf", "19", "-preset", "slow", "-pix_fmt", "yuv420p", "-r", "25", "-aspect", "4:3", str(out))
    projected = max(time.monotonic() - start, 0.001) * source_duration / 3600
    (r.workdir / "review" / "encode-projection.txt").write_text(f"Projected full-run time: {projected:.2f} hours\n")
    if projected > 24:
        raise SystemExit(f"Projected full-run encode time is {projected:.2f} hours; stop-and-ask condition applies.")
    return projected


def remux_and_qc(r: Runner, source_data: dict) -> None:
    chapters = r.workdir / "output" / "chapters.xml"
    r.run(("mkvextract", str(r.source), "chapters", str(chapters)))
    final = r.workdir / "output" / "The Garden (Wiseman, 2005) [restored].mkv"
    r.run(("mkvmerge", "-o", str(final), "--chapters", str(chapters), str(r.workdir / "output" / "video_clean.mkv"), "--sync", "0:-21", str(r.workdir / "audio_clean.m4a")))
    r.ffmpeg("-v", "error", "-i", str(final), "-f", "null", "-")
    final_probe = r.ffprobe("-v", "error", "-show_format", "-show_streams", "-of", "json", str(final), capture=True)
    (r.workdir / "review" / "final-ffprobe.json").write_text(final_probe.stdout)
    if abs(duration(json.loads(final_probe.stdout)) - duration(source_data)) > 0.1:
        raise RuntimeError("Final duration differs from source by more than 100 ms")
    final_review = r.workdir / "review" / "final"
    final_review.mkdir(exist_ok=True)
    chapter_text = chapters.read_text()
    chapter_times = []
    for value in re.findall(r'<ChapterTimeStart>([^<]+)</ChapterTimeStart>', chapter_text):
        hours, minutes, seconds = value.split(":")
        chapter_times.append(int(hours) * 3600 + int(minutes) * 60 + float(seconds))
    for chapter_number in (1, 14, 27):
        if len(chapter_times) >= chapter_number:
            timestamp = chapter_times[chapter_number - 1]
            r.ffmpeg("-ss", str(timestamp), "-i", str(final), "-t", "5", "-c", "copy", str(final_review / f"sync-chapter-{chapter_number:02d}.mkv"))
    for i, timestamp in enumerate(BASELINE_TIMES, 1):
        for stem, media in (("before", r.source), ("after", final)):
            r.ffmpeg("-ss", str(timestamp), "-i", str(media), "-frames:v", "1", str(final_review / f"frame-{i:02d}-{stem}.png"))
    for stem, media in (("before", r.workdir / "audio_src.wav"), ("after", r.workdir / "audio_clean.wav")):
        r.ffmpeg("-ss", "30", "-i", str(media), "-t", "30", "-lavfi", "showspectrumpic=s=1280x720:legend=disabled", str(final_review / f"spectrogram-{stem}.png"))


def write_report(r: Runner, method: str, projection: float | None, completed: bool) -> None:
    versions = {}
    for tool in ("ffmpeg", "ffprobe", "sox", "mkvmerge", "mediainfo", "deep-filter"):
        if shutil.which(tool):
            result = subprocess.run((tool, "--version"), capture_output=True, text=True)
            versions[tool] = ((result.stdout or result.stderr).splitlines() or ["available"])[0]
    report = ["# Restoration report", "", f"Status: {'complete' if completed else 'sample gate pending'}", "", "## Tools", "", "```json", json.dumps(versions, indent=2), "```", "", "## Settings", "", f"Audio method: `{method}`", f"Video filter: `{video_filter()}`", "Video: `libx264 -crf 19 -preset slow -pix_fmt yuv420p -r 25 -aspect 4:3`", "Audio: `aac -b:a 192k`; remux delay: `--sync 0:-21`", "", "## Executed commands", "", "```sh"]
    report.extend(r.commands)
    report.extend(["```", "", "## Review gate", "", "Inspect `baseline/combing-check-*.png` for combing and all sample source/filtered pairs for waxiness, ghosting, banding, texture loss, and ambience loss. SSIM logs are guardrails, not optimization targets.", "", f"Projected full-run time: {projection:.2f} hours" if projection is not None else "Projected full-run time: not measured", ""])
    (r.workdir / "RESTORATION_REPORT.md").write_text("\n".join(report))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--workdir", type=Path, required=True)
    parser.add_argument("--audio-method", choices=("auto", "deepfilter", "sox"), default="auto")
    parser.add_argument("--approve-samples", action="store_true")
    parser.add_argument("--full", action="store_true")
    args = parser.parse_args(argv)
    require_tools(("ffmpeg", "ffprobe", "sox", "mkvmerge", "mkvextract"))
    if not args.source.is_file():
        raise SystemExit(f"Source does not exist: {args.source}")
    safe_workdir(args.source, args.workdir)
    runner = Runner(args.source.resolve(), args.workdir.resolve(), [])
    source_data = probe(runner)
    validate_source(source_data)
    phase_one(runner, source_data)
    extract_samples(runner)
    method = audio_restore(runner, args.audio_method)
    video_samples(runner)
    if not (args.approve_samples and args.full):
        write_report(runner, method, None, False)
        print("Sample outputs are ready. Review them, then rerun with --approve-samples --full.")
        return 0
    projection = full_encode(runner, duration(source_data))
    remux_and_qc(runner, source_data)
    write_report(runner, method, projection, True)
    print(runner.workdir / "output" / "The Garden (Wiseman, 2005) [restored].mkv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
