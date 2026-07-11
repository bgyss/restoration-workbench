#!/usr/bin/env python3
"""Run fixed FFmpeg output-QC diagnostics and write a JSON record."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from comfyui_restoration.validation import run_qc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("media", type=Path)
    parser.add_argument("record", type=Path)
    args = parser.parse_args()
    result = run_qc(str(args.media))
    args.record.parent.mkdir(parents=True, exist_ok=True)
    args.record.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["observations"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
