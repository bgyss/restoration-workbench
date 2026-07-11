"""Small API-first service facade suitable for an MCP bridge or fake client tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .agent import AgentRequest
from .doctor import report
from .execution import Approval, ResumableRun, candidate_hash
from .media import ingest
from .core import write_json
from .media import ffprobe, run_command
from .review import build_review_bundle
from .sampling import plan_samples as build_sample_plan
from .candidates import audio_candidate_matrix, record_candidate
from .report import export_json, export_markdown
from .remux import validation_command, compare_streams
from .validation import run_qc, validate_invariants
from .analysis import analyze_probe
from .video_candidates import candidate_catalog


class RestorationService:
    def __init__(self, workspace: Path):
        self.workspace = workspace.resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)
        self._idempotent: dict[str, Any] = {}

    def _request(self, operation: str, key: str, relative_path: str | None = None) -> AgentRequest:
        request = AgentRequest(operation, key, self.workspace, relative_path)
        request.validate()
        if key in self._idempotent:
            if self._idempotent[key]["operation"] != operation:
                raise ValueError("idempotency key was used for a different operation")
            return request
        self._idempotent[key] = {"operation": operation}
        return request

    @staticmethod
    def _approval_value(value: Approval | dict) -> Approval:
        if isinstance(value, Approval):
            return value
        if not isinstance(value, dict):
            raise ValueError("approval must be an approval record object")
        try:
            approval = Approval(
                str(value["candidate_hash"]), str(value["reviewer"]),
                tuple(value["decisions"]), str(value.get("authority", "human")),
            )
        except (KeyError, TypeError) as error:
            raise ValueError("malformed approval record") from error
        approval.validate()
        return approval

    def inspect_restoration_capabilities(self, key: str) -> dict:
        self._request("inspect_restoration_capabilities", key)
        capabilities = report()
        capabilities["video_candidates"] = candidate_catalog()
        return capabilities

    def probe_media(self, key: str, relative_path: str) -> dict:
        request = self._request("probe_media", key, relative_path)
        source = ingest(request.validate() or Path(relative_path), self.workspace)
        return {"path": source.path, "identity": source.identity, "probe": source.probe, "analysis": analyze_probe(source.probe)}

    def plan_samples(self, key: str, duration_seconds: float) -> dict:
        self._request("plan_samples", key)
        if not 1 <= duration_seconds <= 24 * 60 * 60:
            raise ValueError("duration is outside bounded planning limits")
        return {"samples": build_sample_plan(duration_seconds), "seed": 0}

    def build_review_bundle(self, key: str, source: str, candidates: list[dict]) -> str:
        self._request("build_review_bundle", key)
        return str(build_review_bundle(self.workspace, source=source, candidates=candidates))

    def list_candidates(self, key: str) -> list[dict]:
        self._request("list_candidates", key)
        return audio_candidate_matrix() + [{"domain": "video", **candidate} for candidate in candidate_catalog()]

    def run_sample_candidates(self, key: str, metrics_by_id: dict[str, dict]) -> list[dict]:
        self._request("run_sample_candidates", key)
        known = {candidate["id"]: candidate for candidate in audio_candidate_matrix()}
        unknown = set(metrics_by_id) - set(known)
        if unknown:
            raise ValueError(f"unknown candidate ids: {sorted(unknown)}")
        results = [record_candidate(known[item], metrics=metrics_by_id[item]) for item in sorted(metrics_by_id)]
        write_json(self.workspace / "review" / "candidate-results.json", {"schema_version": "1", "candidates": results})
        return results

    def record_human_approval(self, key: str, parameters: dict, reviewer: str, decisions: list[dict]) -> dict:
        self._request("record_human_approval", key)
        if not reviewer.strip() or not decisions:
            raise ValueError("reviewer and decisions are required")
        approval = Approval(candidate_hash(parameters), reviewer, tuple(decisions))
        approval.validate()
        path = self.workspace / "review" / "approval.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"candidate_hash": approval.candidate_hash, "reviewer": reviewer, "decisions": decisions, "authority": "human"}, indent=2) + "\n")
        return json.loads(path.read_text())

    def run_approved_full_restoration(self, key: str, run_id: str, parameters: dict, approval: Approval | dict, chunks: list[str]) -> dict:
        self._request("run_approved_full_restoration", key)
        approval_record = self._approval_value(approval)
        return ResumableRun(self.workspace, run_id, parameters).execute(chunks, lambda chunk: f"runs/{run_id}/{chunk}.done", approval_record)

    def get_run_status(self, key: str, run_id: str) -> dict:
        self._request("get_run_status", key)
        return ResumableRun(self.workspace, run_id, {}).status()

    def cancel_run(self, key: str, run_id: str) -> dict:
        self._request("cancel_run", key)
        return ResumableRun(self.workspace, run_id, {}).cancel()

    def validate_output(self, key: str, relative_path: str, source_probe: dict | None = None, include_qc: bool = False) -> dict:
        request = self._request("validate_output", key, relative_path)
        path = request.validate()
        assert path is not None
        run_command(validation_command(path))
        output_probe = ffprobe(path)
        result = {"decode_ok": True, "probe": output_probe}
        qc = run_qc(str(path)) if include_qc else None
        if qc is not None:
            result["qc"] = qc
        if source_probe is not None:
            result["preservation"] = compare_streams(source_probe, output_probe)
            result["invariants"] = validate_invariants(source_probe, output_probe, qc=qc["observations"] if qc else None)
            if not result["invariants"]["valid"]:
                raise ValueError(f"output validation failed: {result['invariants']['failures']}")
        return result

    def export_restoration_report(self, key: str, source_json: str, destination: str) -> str:
        self._request("export_restoration_report", key, source_json)
        source = self.workspace / source_json
        output = self.workspace / destination
        export_json(source, output.with_suffix(".json"), self.workspace)
        export_markdown(source, output.with_suffix(".md"), self.workspace)
        return destination
