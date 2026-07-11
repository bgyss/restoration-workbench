from pathlib import Path

import pytest

from comfyui_restoration.agent import AgentRequest
from comfyui_restoration.agent import OPERATIONS
from comfyui_restoration.fake_client import FakeAgentClient
from comfyui_restoration.service import RestorationService


def test_agent_contract_rejects_unknown_operation_and_escape(tmp_path: Path):
    with pytest.raises(ValueError):
        AgentRequest("run_shell", "1", tmp_path).validate()
    with pytest.raises(ValueError):
        AgentRequest("probe_media", "1", tmp_path, "../source.mkv").validate()


def test_agent_contract_requires_idempotency_key(tmp_path: Path):
    with pytest.raises(ValueError):
        AgentRequest("probe_media", "", tmp_path).validate()


def test_fake_client_has_a_service_method_for_every_declared_operation(tmp_path: Path):
    service = RestorationService(tmp_path)
    client = FakeAgentClient(service)
    assert all(callable(getattr(service, operation, None)) for operation in OPERATIONS)
    with pytest.raises(ValueError):
        client.call("run_shell", idempotency_key="x")
