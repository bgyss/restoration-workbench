#!/usr/bin/env python3
"""Generate a tiny local fixture and exercise the conservative media lane."""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from comfyui_restoration.audio import repair_command
from comfyui_restoration.media import run_command, tool_path
from comfyui_restoration.video import baseline_command


def main() -> int:
    root = Path(tempfile.mkdtemp(prefix="restoration-e2e-"))
    try:
        source = root / "source.mkv"
        audio = root / "audio.wav"
        video = root / "video.mkv"
        run_command((tool_path("ffmpeg"), "-hide_banner", "-y", "-f", "lavfi", "-i", "testsrc=size=64x48:rate=5", "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000", "-t", "1", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "pcm_s16le", str(source)))
        run_command(tuple(repair_command(source, audio, method="bypass")))
        run_command(tuple(baseline_command(source, video, crf=19)))
        print(f"tiny e2e passed: {source.name}, {audio.name}, {video.name}")
        return 0
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
