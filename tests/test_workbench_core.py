import json
from pathlib import Path

import pytest

from comfyui_restoration.core import workspace_path
from comfyui_restoration.core import load_manifest
from comfyui_restoration.execution import Approval, ResumableRun, candidate_hash
from comfyui_restoration.policy import validate_sample_window
from comfyui_restoration.remux import compare_streams


def test_workspace_rejects_traversal_and_symlink(tmp_path: Path):
    root = tmp_path / "work"
    root.mkdir()
    with pytest.raises(ValueError):
        workspace_path(Path("../outside.mkv"), root)
    link = root / "link"
    link.symlink_to(tmp_path)
    with pytest.raises(ValueError):
        workspace_path(link, root)


def test_resumable_run_requires_matching_human_approval(tmp_path: Path):
    params = {"branch": "faithful", "crf": 19}
    run = ResumableRun(tmp_path, "one", params)
    with pytest.raises(PermissionError):
        run.execute(["a"], lambda _: "x")
    approval = Approval(candidate_hash(params), "reviewer", ({"sample": "A", "decision": "approve"},))
    state = run.execute(["a", "b"], lambda chunk: chunk + ".mkv", approval)
    assert state["status"] == "complete"
    assert json.loads((tmp_path / "runs/one/state.json").read_text())["completed"] == ["a", "b"]
    resumed = run.execute(["a", "b", "c"], lambda chunk: chunk + ".mkv", approval)
    assert resumed["completed"] == ["a", "b", "c"]


def test_resumable_run_persists_running_state_before_worker(tmp_path: Path):
    params = {"branch": "faithful"}
    run = ResumableRun(tmp_path, "running", params)
    approval = Approval(candidate_hash(params), "reviewer", ({"sample": "A", "decision": "approve"},))
    observed = []
    run.execute(["a"], lambda chunk: observed.append(json.loads((tmp_path / "runs/running/state.json").read_text())["status"]) or "done", approval)
    assert observed == ["running"]


def test_sample_window_is_bounded():
    validate_sample_window(1, 2, 10)
    with pytest.raises(ValueError):
        validate_sample_window(9, 2, 10)


def test_stream_comparison_reports_preservation_guardrail():
    probe = {"format": {"duration": "10"}, "streams": [{"codec_type": "video"}, {"codec_type": "audio"}]}
    result = compare_streams(probe, probe)
    assert result["stream_count_preserved"] is True


def test_manifest_loader_rejects_escape_and_malformed_data(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text('{"schema_version":"1","status":"bogus"}')
    with pytest.raises(ValueError, match="malformed"):
        load_manifest(manifest, root=tmp_path)
