"""Visual-review-based, resumable execution primitives."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .core import RunManifest, write_manifest
from .resources import resource_preflight


@dataclass(frozen=True)
class Approval:
    candidate_hash: str
    reviewer: str
    decisions: tuple[dict, ...]
    authority: str = "human"
    def validate(self) -> None:
        if self.authority != "human" or not self.reviewer.strip() or not self.decisions:
            raise ValueError("a non-empty human visual-review record is required")


def candidate_hash(parameters: dict) -> str:
    payload = json.dumps(parameters, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


class ResumableRun:
    def __init__(self, root: Path, run_id: str, parameters: dict):
        self.root = root.resolve()
        self.run_id = run_id
        self.parameters = parameters
        self.state_path = self.root / "runs" / run_id / "state.json"
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

    def _state(self) -> dict:
        if not self.state_path.exists():
            return {"run_id": self.run_id, "status": "planned", "completed": [], "parameters": self.parameters}
        return json.loads(self.state_path.read_text())

    def status(self) -> dict:
        return self._state()

    def cancel(self) -> dict:
        state = self._state()
        if state.get("status") == "complete":
            raise ValueError("completed runs cannot be cancelled")
        state["status"] = "cancelled"
        self.state_path.write_text(json.dumps(state, indent=2) + "\n")
        return state

    def execute(self, chunks: list[str], worker: Callable[[str], str], approval: Approval | None = None) -> dict:
        if approval is None:
            raise PermissionError("full execution requires a human visual-review record")
        approval.validate()
        if approval.candidate_hash != candidate_hash(self.parameters):
            raise ValueError("review is for different candidate parameters")
        estimate = self.parameters.get("estimated_storage_bytes")
        preflight = None
        if estimate is not None:
            preflight = resource_preflight(
                self.root,
                estimated_bytes=int(estimate),
                min_free_bytes=int(self.parameters.get("min_free_bytes", 0)),
                max_chunks=int(self.parameters.get("max_chunks", 10_000)),
                chunk_count=len(chunks),
            )
            if not preflight["within_bounds"]:
                raise RuntimeError("insufficient free storage for approved run")
        state = self._state()
        state["status"] = "running"
        state["approval"] = {"reviewer": approval.reviewer, "candidate_hash": approval.candidate_hash}
        if preflight is not None:
            state["resource_preflight"] = preflight
        if "projected_seconds" in self.parameters:
            state["timing_projection"] = {"projected_seconds": float(self.parameters["projected_seconds"]), "source": "approved_parameters"}
        self.state_path.write_text(json.dumps(state, indent=2) + "\n")
        cancelled = False
        for chunk in chunks:
            if self._state().get("status") == "cancelled":
                cancelled = True
                break
            if chunk in state["completed"]:
                continue
            state.setdefault("events", []).append({"event": "started", "chunk": chunk, "time": time.time()})
            try:
                output = worker(chunk)
            except Exception as error:
                state["status"] = "failed"
                state.setdefault("events", []).append({"event": "failed", "chunk": chunk, "error": type(error).__name__, "message": str(error), "time": time.time()})
                self.state_path.write_text(json.dumps(state, indent=2) + "\n")
                write_manifest(self.state_path.with_name("run-manifest.json"), RunManifest(self.run_id, "failed", str(self.root), outputs=tuple(state.get("outputs", {}).values()), parameters_hash=candidate_hash(self.parameters), events=tuple(state.get("events", [])), started_at=next((event["time"] for event in state.get("events", []) if event.get("event") == "started"), None), finished_at=time.time()))
                raise
            state["completed"].append(chunk)
            state.setdefault("outputs", {})[chunk] = output
            if self._state().get("status") == "cancelled":
                cancelled = True
                state["status"] = "cancelled"
            self.state_path.write_text(json.dumps(state, indent=2) + "\n")
            if cancelled:
                break
        state["status"] = "cancelled" if cancelled else "complete"
        self.state_path.write_text(json.dumps(state, indent=2) + "\n")
        write_manifest(self.state_path.with_name("run-manifest.json"), RunManifest(self.run_id, state["status"], str(self.root), outputs=tuple(state.get("outputs", {}).values()), parameters_hash=candidate_hash(self.parameters), events=tuple(state.get("events", [])), started_at=next((event["time"] for event in state.get("events", []) if event.get("event") == "started"), None), finished_at=time.time()))
        return state
