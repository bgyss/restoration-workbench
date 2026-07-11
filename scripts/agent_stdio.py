#!/usr/bin/env python3
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from comfyui_restoration.stdio_server import StdioAgentServer


workspace = Path(sys.argv[1]) if len(sys.argv) == 2 else Path("work")
secret = os.environ.get("COMFYUI_RESTORATION_APPROVAL_SECRET")
StdioAgentServer(workspace, approval_secret=secret.encode() if secret else None).serve()
