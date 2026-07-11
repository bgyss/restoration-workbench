from pathlib import Path

import pytest

from comfyui_restoration.benchmark import FIXTURES, fixture_command, manifest
from comfyui_restoration.service import RestorationService
from comfyui_restoration.execution import Approval, candidate_hash


def test_synthetic_manifest_has_rights_and_pinned_fixtures():
    data = manifest()
    assert data["rights"]
    assert {item["name"] for item in data["fixtures"]} == {item.name for item in FIXTURES}


def test_service_idempotency_and_approval_boundary(tmp_path: Path):
    service = RestorationService(tmp_path)
    assert service.plan_samples("one", 100)["seed"] == 0
    with pytest.raises(ValueError):
        service.inspect_restoration_capabilities("one")
    with pytest.raises(ValueError):
        service.record_human_approval("approval", {"branch": "faithful"}, "", [{"decision": "approve"}])


def test_fixture_command_is_explicit():
    command = fixture_command(Path("fixture.mkv"), FIXTURES[0])
    assert "-f" in command and "fixture.mkv" in command


def test_service_approval_run_status_and_cancel(tmp_path: Path):
    service = RestorationService(tmp_path, approval_secret=b"test-secret")
    parameters = {"branch": "faithful"}
    approval = Approval(candidate_hash(parameters), "reviewer", ({"sample": "A", "decision": "approve"},))
    signature = approval.signature(b"test-secret")
    state = service.run_approved_full_restoration("run", "r1", parameters, approval, ["A"], signature)
    assert state["status"] == "complete"
    assert service.get_run_status("status", "r1")["status"] == "complete"
    with pytest.raises(ValueError):
        service.cancel_run("cancel", "r1")


def test_service_cannot_forge_or_use_unsigned_approval(tmp_path: Path):
    service = RestorationService(tmp_path, approval_secret=b"host-secret")
    with pytest.raises(PermissionError):
        service.record_human_approval("approval", {"branch": "faithful"}, "reviewer", [{"decision": "approve"}], "bad")


def test_service_accepts_json_approval_record_for_stdio_round_trip(tmp_path: Path):
    service = RestorationService(tmp_path, approval_secret=b"host-secret")
    parameters = {"branch": "faithful"}
    approval = Approval(candidate_hash(parameters), "reviewer", ({"sample": "A", "decision": "approve"},))
    signature = approval.signature(b"host-secret")
    record = {"candidate_hash": approval.candidate_hash, "reviewer": approval.reviewer, "decisions": list(approval.decisions), "authority": "human", "signature": signature}
    state = service.run_approved_full_restoration("json-run", "r2", parameters, record, ["A"])
    assert state["status"] == "complete"


def test_sample_candidate_results_are_persisted_for_review(tmp_path: Path):
    service = RestorationService(tmp_path)
    results = service.run_sample_candidates("candidates", {"untouched": {"peak": -2.0}})
    record = (tmp_path / "review" / "candidate-results.json").read_text()
    assert results[0]["id"] == "untouched"
    assert '"candidates"' in record
    assert '"peak": -2.0' in record


def test_validate_output_can_include_structured_qc(monkeypatch, tmp_path: Path):
    output = tmp_path / "output.mkv"
    output.write_bytes(b"placeholder")
    monkeypatch.setattr("comfyui_restoration.service.run_command", lambda _: None)
    monkeypatch.setattr("comfyui_restoration.service.ffprobe", lambda _: {"streams": [], "format": {}})
    monkeypatch.setattr("comfyui_restoration.service.run_qc", lambda _: {"observations": {"freeze_events": 0}})
    result = RestorationService(tmp_path).validate_output("qc", "output.mkv", include_qc=True)
    assert result["qc"]["observations"]["freeze_events"] == 0
