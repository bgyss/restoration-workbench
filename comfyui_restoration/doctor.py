"""Machine-readable local capability report."""

from __future__ import annotations

import json
import shutil
import subprocess
from .adapters.audio_models import available_audio_adapters


def _version(name: str) -> str | None:
    path = shutil.which(name)
    if not path:
        return None
    result = subprocess.run((path, "-version"), capture_output=True, text=True)
    return (result.stdout or result.stderr).splitlines()[0] if result.returncode == 0 else "available"


def report() -> dict:
    return {"tools": {name: _version(name) for name in ("ffmpeg", "ffprobe", "mkvmerge", "sox")}, "audio_adapters": available_audio_adapters(), "comfyui": "optional host; install separately", "policy": {"paid_service_required": False, "generative_default": False, "full_run_requires_human_approval": True}}


def main() -> int:
    print(json.dumps(report(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
