from pathlib import Path

import pytest

from comfyui_restoration.workflows import validate_node_exports, validate_workflow, validate_workflows


WORKFLOWS = Path(__file__).parents[1] / "examples" / "workflows"


def test_checked_in_workflows_cover_review_and_full_contract():
    inventory = validate_workflows(WORKFLOWS)
    assert len(inventory) == 6
    assert "RestorationLoadMedia" in inventory["generic_restoration_review_api.json"]
    assert "HumanApprovalGate" in inventory["generic_restoration_full_api.json"]


def test_workflow_validator_rejects_incomplete_review_graph(tmp_path: Path):
    path = tmp_path / "generic_restoration_review_api.json"
    path.write_text('{"1": {"class_type": "RestorationLoadMedia", "inputs": {}}}\n')
    with pytest.raises(ValueError, match="missing required"):
        validate_workflow(path)


def test_workflow_validator_rejects_unexported_api_node():
    with pytest.raises(ValueError, match="unexported"):
        validate_node_exports({"1": {"class_type": "UnknownNode", "inputs": {}}})
