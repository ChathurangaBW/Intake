from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class StaticWorkerRequest:
    worker_id: str
    tool_call_id: str
    artifact_id: str
    profile: str = "standard"
    timeout_seconds: int = 900
    environment: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class StaticWorkerResult:
    worker_id: str
    tool_call_id: str
    status: str
    summary: str
    evidence: list[dict[str, Any]] = field(default_factory=list)


class StaticWorkerClient:
    """Interface for rootless container workers.

    Implementations should mount inputs read-only, disable network by default,
    enforce CPU/memory/time budgets, and destroy scratch state after completion.
    """

    async def submit(self, request: StaticWorkerRequest) -> StaticWorkerResult:
        raise NotImplementedError("static worker backend is not configured")
