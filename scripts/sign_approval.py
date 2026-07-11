#!/usr/bin/env python3
"""Sign an existing human decision using the host-held approval secret."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: sign_approval.py work/garden-probe/approval-dsp-afftdn.json")
    path = Path(sys.argv[1])
    secret = os.environ.get("COMFYUI_RESTORATION_APPROVAL_SECRET")
    if not secret:
        raise SystemExit("COMFYUI_RESTORATION_APPROVAL_SECRET is not configured")
    data = json.loads(path.read_text())
    payload = json.dumps({"candidate_hash": data["candidate_hash"], "reviewer": data["reviewer"], "decisions": data.get("decisions", [{"decision": data["decision"]}]), "authority": data["authority"]}, sort_keys=True, separators=(",", ":")).encode()
    data["signature"] = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    data["status"] = "approved"
    data["full_run_authorized"] = True
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
