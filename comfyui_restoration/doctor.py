"""Machine-readable local capability report."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
import os
from .adapters.audio_models import available_audio_adapters


def _version(name: str) -> str | None:
    path = shutil.which(name)
    if not path:
        return None
    result = subprocess.run((path, "-version"), capture_output=True, text=True)
    return (result.stdout or result.stderr).splitlines()[0] if result.returncode == 0 else "available"


def _gpu_report() -> dict[str, str | bool | None]:
    for command in ("nvidia-smi", "rocm-smi"):
        path = shutil.which(command)
        if path:
            result = subprocess.run((path, "--query-gpu=name,memory.total", "--format=csv,noheader") if command == "nvidia-smi" else (path,), capture_output=True, text=True)
            return {"available": result.returncode == 0, "backend": command, "summary": result.stdout.strip() or result.stderr.strip()}
    return {"available": False, "backend": None, "summary": None}


def report() -> dict:
    audio = available_audio_adapters()
    return {
        "tools": {name: _version(name) for name in ("ffmpeg", "ffprobe", "mkvmerge", "sox")},
        "audio_adapters": audio,
        "model_hashes": {},
        "comfyui": {"version": os.environ.get("COMFYUI_VERSION"), "status": "optional host; install separately"},
        "node_version": "0.1.0",
        "gpu": _gpu_report(),
        "disk": {"path": str(Path.cwd()), "free_bytes": shutil.disk_usage(Path.cwd()).free},
        "incompatible_optional_branches": [name for name, available in audio.items() if not available],
        "policy": {"paid_service_required": False, "generative_default": False, "desktop_full_run_requires_visual_review": True, "agent_full_run_requires_signed_approval": True},
    }


def main() -> int:
    print(json.dumps(report(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
