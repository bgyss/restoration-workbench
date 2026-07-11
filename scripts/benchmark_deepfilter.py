#!/usr/bin/env python3
"""Run an opt-in DeepFilterNet benchmark without substituting the DSP baseline."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from comfyui_restoration.adapters.audio_models import AudioModelRequest, command
from comfyui_restoration.media import run_command
from comfyui_restoration.metrics import pcm_metrics


def _hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def benchmark(source: Path, output: Path, record: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    result: dict = {"adapter": "deepfilternet", "source": source.name, "source_sha256": _hash(source)}
    runner = shutil.which("deep-filter")
    if runner is None:
        result.update({"status": "unavailable", "reason": "deep-filter runner is not installed"})
    else:
        version = subprocess.run((runner, "--version"), capture_output=True, text=True)
        request = AudioModelRequest("deepfilternet", source, output / source.name, bypass=False)
        args = command(request)
        run_command(args)
        candidates = sorted(output.glob("*.wav"))
        if not candidates:
            result.update({"status": "failed", "reason": "runner produced no WAV output", "command": args})
        else:
            produced = candidates[0]
            result.update({"status": "complete", "command": args, "version": (version.stdout or version.stderr).strip(), "output": produced.name, "output_sha256": _hash(produced), "metrics": pcm_metrics(produced)})
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: benchmark_deepfilter.py INPUT.wav OUTPUT_DIR RECORD.json")
    print(json.dumps(benchmark(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])), indent=2))
