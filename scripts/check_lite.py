#!/usr/bin/env python3
"""Run deterministic checks that do not require pytest or model downloads."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(args: list[str]) -> None:
    subprocess.run(args, cwd=ROOT, check=True)


def main() -> int:
    run(["ruff", "check", "comfyui_restoration", "scripts", "tests"])
    run([sys.executable, "-m", "compileall", "-q", "comfyui_restoration", "scripts", "tests"])
    for path in list((ROOT / "examples").rglob("*.json")) + list((ROOT / "comfyui_restoration" / "schemas").glob("*.json")):
        json.loads(path.read_text())
    run([sys.executable, "scripts/audit_public.py"])
    run([sys.executable, "scripts/test_e2e_small.py"])
    print("check-lite passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
