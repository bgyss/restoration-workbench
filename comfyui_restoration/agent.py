"""Framework-neutral agent operation contract.

This module is deliberately not an MCP server. It defines the safe operation names and validates
requests so an MCP implementation can be swapped in without changing media policy.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .core import workspace_path

OPERATIONS = (
    "inspect_restoration_capabilities", "probe_media", "plan_samples", "run_sample_candidates",
    "get_run_status", "cancel_run", "list_candidates", "build_review_bundle",
    "record_human_approval", "run_approved_full_restoration", "validate_output",
    "export_restoration_report",
)


@dataclass(frozen=True)
class AgentRequest:
    operation: str
    idempotency_key: str
    workspace: Path
    relative_path: str | None = None

    def validate(self) -> Path | None:
        if self.operation not in OPERATIONS:
            raise ValueError("unknown restoration operation")
        if not self.idempotency_key.strip():
            raise ValueError("idempotency key is required")
        if self.relative_path is None:
            return None
        return workspace_path(Path(self.relative_path), self.workspace)

