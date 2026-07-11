"""Tiny fake transport used by MCP contract tests."""

from __future__ import annotations

from typing import Any, Callable

from .agent import OPERATIONS


class FakeAgentClient:
    def __init__(self, service: Any):
        self.service = service
        self.calls: list[dict[str, Any]] = []

    def call(self, operation: str, **arguments: Any) -> Any:
        if operation not in OPERATIONS:
            raise ValueError("unknown restoration operation")
        method: Callable[..., Any] = getattr(self.service, operation)
        self.calls.append({"operation": operation, "arguments": sorted(arguments)})
        return method(**arguments)

