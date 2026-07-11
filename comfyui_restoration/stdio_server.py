"""JSON-lines agent transport for MCP bridges and local automation.

Each input line is one JSON object: ``{"id": 1, "operation": "...", "arguments": {...}}``.
The server never evaluates code or shell text; it dispatches only declared service methods.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TextIO

from .agent import OPERATIONS
from .service import RestorationService


class StdioAgentServer:
    def __init__(self, workspace: Path):
        self.service = RestorationService(workspace)

    def handle(self, request: dict) -> dict:
        request_id = request.get("id")
        try:
            operation = request.get("operation")
            if operation not in OPERATIONS:
                raise ValueError("unknown restoration operation")
            arguments = request.get("arguments", {})
            if not isinstance(arguments, dict):
                raise ValueError("arguments must be an object")
            result = getattr(self.service, operation)(**arguments)
            return {"id": request_id, "ok": True, "result": result}
        except (TypeError, ValueError, PermissionError, RuntimeError) as error:
            return {"id": request_id, "ok": False, "error": {"type": type(error).__name__, "message": str(error)}}

    def serve(self, input_stream: TextIO = sys.stdin, output_stream: TextIO = sys.stdout) -> None:
        for line in input_stream:
            if not line.strip():
                continue
            try:
                request = json.loads(line)
                response = self.handle(request)
            except json.JSONDecodeError as error:
                response = {"id": None, "ok": False, "error": {"type": "JSONDecodeError", "message": str(error)}}
            output_stream.write(json.dumps(response, sort_keys=True) + "\n")
            output_stream.flush()
