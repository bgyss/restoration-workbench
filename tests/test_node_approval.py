from pathlib import Path

import pytest

from comfyui_restoration.execution import Approval, candidate_hash
from comfyui_restoration.nodes import HumanApprovalGate, ResumableFullRun


def test_node_approval_requires_host_secret(monkeypatch):
    monkeypatch.delenv("COMFYUI_RESTORATION_APPROVAL_SECRET", raising=False)
    with pytest.raises(PermissionError):
        HumanApprovalGate().approve("{}", "human", '[{"decision":"approve"}]', "")


def test_signed_node_approval_can_be_consumed(monkeypatch, tmp_path: Path):
    secret = b"node-secret"
    monkeypatch.setenv("COMFYUI_RESTORATION_APPROVAL_SECRET", secret.decode())
    parameters = {"branch": "faithful"}
    approval = Approval(candidate_hash(parameters), "human", ({"decision": "approve"},))
    signed = approval.signature(secret)
    result = HumanApprovalGate().approve("{\"branch\":\"faithful\"}", "human", '[{"decision":"approve"}]', signed)[0]
    assert result.signature_value == signed
    state = ResumableFullRun().start(str(tmp_path), "r", '{"branch":"faithful"}', result, '["a"]')[0]
    assert state["status"] == "complete"
