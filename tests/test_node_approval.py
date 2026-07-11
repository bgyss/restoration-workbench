from pathlib import Path

from comfyui_restoration.nodes import HumanApprovalGate, ResumableFullRun


def test_desktop_node_approval_is_visual_only():
    result = HumanApprovalGate().approve("{}", "human", '[{"decision":"approve"}]')[0]
    assert result.authority == "human"


def test_desktop_visual_approval_can_start_run_without_secret(tmp_path: Path):
    result = HumanApprovalGate().approve("{\"branch\":\"faithful\"}", "human", '[{"decision":"approve"}]')[0]
    state = ResumableFullRun().start(str(tmp_path), "r", '{"branch":"faithful"}', result, '["a"]')[0]
    assert state["status"] == "complete"
