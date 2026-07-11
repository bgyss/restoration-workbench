from pathlib import Path

from comfyui_restoration.public_audit import audit_git_history


def test_history_audit_returns_a_list_for_repository(tmp_path: Path):
    # A non-repository is reported as an inspection failure, never as an exception.
    assert audit_git_history(tmp_path) == ["unable to inspect Git history"]
