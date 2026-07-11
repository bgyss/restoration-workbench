from pathlib import Path

import pytest

from comfyui_restoration.agent import AgentRequest


def test_agent_contract_rejects_unknown_operation_and_escape(tmp_path: Path):
    with pytest.raises(ValueError):
        AgentRequest("run_shell", "1", tmp_path).validate()
    with pytest.raises(ValueError):
        AgentRequest("probe_media", "1", tmp_path, "../source.mkv").validate()


def test_agent_contract_requires_idempotency_key(tmp_path: Path):
    with pytest.raises(ValueError):
        AgentRequest("probe_media", "", tmp_path).validate()
