"""Approval-gated, resumable execution primitives."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .core import RunManifest, write_manifest


@dataclass(frozen=True)
class Approval:
    candidate_hash: str
    reviewer: str
    decisions: tuple[dict, ...]
    authority: str = "human"
    signature_value: str | None = None

    def signing_payload(self) -> bytes:
        return json.dumps({"candidate_hash": self.candidate_hash, "reviewer": self.reviewer, "decisions": self.decisions, "authority": self.authority}, sort_keys=True, separators=(",", ":")).encode()

    def signature(self, secret: bytes) -> str:
        return hmac.new(secret, self.signing_payload(), hashlib.sha256).hexdigest()

    def verify(self, secret: bytes, signature: str) -> None:
        if not hmac.compare_digest(self.signature(secret), signature):
            raise PermissionError("approval signature is invalid")

    def validate(self) -> None:
        if self.authority != "human" or not self.reviewer.strip() or not self.decisions:
            raise ValueError("a non-empty human approval record is required")


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
            raise PermissionError("full execution requires a human approval artifact")
        approval.validate()
        if approval.candidate_hash != candidate_hash(self.parameters):
            raise ValueError("approval is for different candidate parameters")
        state = self._state()
        state["status"] = "running"
        state["approval"] = {"reviewer": approval.reviewer, "candidate_hash": approval.candidate_hash}
        self.state_path.write_text(json.dumps(state, indent=2) + "\n")
        for chunk in chunks:
            if self._state().get("status") == "cancelled":
                break
            if chunk in state["completed"]:
                continue
            state.setdefault("events", []).append({"event": "started", "chunk": chunk, "time": time.time()})
            output = worker(chunk)
            state["completed"].append(chunk)
            state.setdefault("outputs", {})[chunk] = output
            self.state_path.write_text(json.dumps(state, indent=2) + "\n")
        state["status"] = "complete"
        self.state_path.write_text(json.dumps(state, indent=2) + "\n")
        write_manifest(self.state_path.with_name("run-manifest.json"), RunManifest(self.run_id, state["status"], str(self.root), outputs=tuple(state.get("outputs", {}).values()), parameters_hash=candidate_hash(self.parameters), events=tuple(state.get("events", [])), started_at=next((event["time"] for event in state.get("events", []) if event.get("event") == "started"), None), finished_at=time.time()))
        return state
