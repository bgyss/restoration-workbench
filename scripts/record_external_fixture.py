#!/usr/bin/env python3
"""Record checksum/probe evidence for an authorized local external fixture."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from comfyui_restoration.external_fixtures import record_fixture


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="already-downloaded media outside this repository")
    parser.add_argument("record", type=Path, help="local ignored JSON evidence path")
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--rights-url", required=True)
    parser.add_argument("--license", required=True, dest="license_name")
    args = parser.parse_args()
    evidence = record_fixture(
        args.source, args.record, source_id=args.source_id, source_url=args.source_url,
        rights_url=args.rights_url, license_name=args.license_name,
        repository_root=Path(__file__).resolve().parents[1],
    )
    print(json.dumps({"source_id": evidence["source_id"], "sha256": evidence["sha256"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
