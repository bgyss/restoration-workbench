from pathlib import Path

from comfyui_restoration.public_audit import audit


def test_public_audit_rejects_media_paths_and_credentials(tmp_path: Path):
    (tmp_path / "capture.wav").write_bytes(b"not media")
    (tmp_path / "notes.md").write_text("api_" + "key = 'secret-" + "value'\n")
    failures = audit(tmp_path)
    assert any("media" in failure for failure in failures)
    assert any("credential" in failure for failure in failures)


def test_public_audit_accepts_safe_json(tmp_path: Path):
    (tmp_path / "workflow.json").write_text('{"nodes": []}\n')
    assert audit(tmp_path) == []
