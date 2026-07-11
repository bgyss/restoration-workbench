from pathlib import Path

from comfyui_restoration.execution import Approval, ResumableRun, candidate_hash


def test_run_manifest_contains_parameter_and_timing_evidence(tmp_path: Path):
    parameters = {"branch": "faithful"}
    approval = Approval(candidate_hash(parameters), "human", ({"decision": "approve"},))
    ResumableRun(tmp_path, "evidence", parameters).execute(["a"], lambda _: "a.done", approval)
    text = (tmp_path / "runs/evidence/run-manifest.json").read_text()
    assert "parameters_hash" in text
    assert "started_at" in text
    assert "finished_at" in text
