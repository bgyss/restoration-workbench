import io
import json
from pathlib import Path

from comfyui_restoration.stdio_server import StdioAgentServer


def test_stdio_server_structured_success_and_unknown_operation(tmp_path: Path):
    server = StdioAgentServer(tmp_path)
    success = server.handle({"id": 1, "operation": "plan_samples", "arguments": {"key": "p", "duration_seconds": 100}})
    failure = server.handle({"id": 2, "operation": "run_shell", "arguments": {}})
    assert success["ok"] is True
    assert failure["ok"] is False


def test_stdio_server_handles_malformed_json(tmp_path: Path):
    output = io.StringIO()
    StdioAgentServer(tmp_path).serve(io.StringIO("not json\n"), output)
    response = json.loads(output.getvalue())
    assert response["ok"] is False
    assert response["error"]["type"] == "JSONDecodeError"


def test_stdio_server_has_no_secret_configuration(tmp_path: Path):
    server = StdioAgentServer(tmp_path)
    assert not hasattr(server.service, "_approval_secret")
