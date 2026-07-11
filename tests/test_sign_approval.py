import json
from pathlib import Path

from scripts.sign_approval import main


def test_sign_approval_requires_host_secret(monkeypatch, tmp_path: Path):
    path = tmp_path / "approval.json"
    path.write_text(json.dumps({"candidate_hash": "a" * 64, "reviewer": "human", "decision": "approve", "authority": "human"}))
    monkeypatch.delenv("COMFYUI_RESTORATION_APPROVAL_SECRET", raising=False)
    monkeypatch.setattr("sys.argv", ["sign_approval.py", str(path)])
    try:
        main()
    except SystemExit as error:
        assert "not configured" in str(error)
