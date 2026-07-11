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
    service = RestorationService(tmp_path)
    parameters = {"branch": "faithful"}
    approval = Approval(candidate_hash(parameters), "reviewer", ({"sample": "A", "decision": "approve"},))
    state = service.run_approved_full_restoration("run", "r1", parameters, approval, ["A"])
    assert state["status"] == "complete"
    assert service.get_run_status("status", "r1")["status"] == "complete"
    with pytest.raises(ValueError):
        service.cancel_run("cancel", "r1")
