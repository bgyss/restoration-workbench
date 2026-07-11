#!/usr/bin/env python3
"""Generate a tiny local fixture and exercise the conservative media lane."""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from comfyui_restoration.audio import repair_command
from comfyui_restoration.media import ffprobe, run_command, tool_path
from comfyui_restoration.video import baseline_command
from comfyui_restoration.remux import remux_command, validation_command


def main() -> int:
    root = Path(tempfile.mkdtemp(prefix="restoration-e2e-"))
    try:
        source = root / "source.mkv"
        audio = root / "audio.wav"
        video = root / "video.mkv"
        final = root / "final.mkv"
        run_command((tool_path("ffmpeg"), "-hide_banner", "-y", "-f", "lavfi", "-i", "testsrc=size=64x48:rate=5", "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000", "-t", "1", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "pcm_s16le", str(source)))
        run_command(tuple(repair_command(source, audio, method="bypass")))
        run_command(tuple(baseline_command(source, video, crf=19)))
        run_command(tuple(remux_command(source, video, audio, final)))
        run_command(tuple(validation_command(final)))
        stream_types = [stream.get("codec_type") for stream in ffprobe(final).get("streams", [])]
        if stream_types.count("video") != 1 or stream_types.count("audio") != 1:
            raise RuntimeError(f"unexpected final streams: {stream_types}")
        print(f"tiny e2e passed: {source.name}, {audio.name}, {video.name}, {final.name}")
        return 0
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
