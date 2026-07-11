from pathlib import Path

import pytest

from comfyui_restoration.resources import estimate_storage_bytes, resource_preflight
from comfyui_restoration.execution import Approval, ResumableRun, candidate_hash


def test_storage_estimate_is_positive_and_validates_bounds():
    assert estimate_storage_bytes(10, source_bitrate_bits=8, reserve_bytes=0) == 25
    with pytest.raises(ValueError):
        estimate_storage_bytes(0)


def test_resource_preflight_reports_space_and_rejects_chunk_overflow(tmp_path: Path):
    result = resource_preflight(tmp_path, estimated_bytes=1, chunk_count=1)
    assert result["within_bounds"] is True
    with pytest.raises(ValueError):
        resource_preflight(tmp_path, estimated_bytes=1, chunk_count=2, max_chunks=1)


def test_resumable_state_records_resource_and_timing_evidence(tmp_path: Path):
    parameters = {"estimated_storage_bytes": 1, "projected_seconds": 12.5}
    approval = Approval(candidate_hash(parameters), "human", ({"decision": "approve"},))
    state = ResumableRun(tmp_path, "evidence", parameters).execute(["A"], lambda _: "done", approval)
    assert state["resource_preflight"]["within_bounds"] is True
    assert state["timing_projection"]["projected_seconds"] == 12.5
