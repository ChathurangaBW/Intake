from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DynamicWorkerRequest:
    worker_id: str
    tool_call_id: str
    artifact_id: str
    profile: str = "instrumented"
    timeout_seconds: int = 600
    network_policy: str = "deny_all"
    environment: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class DynamicWorkerResult:
    worker_id: str
    tool_call_id: str
    status: str
    summary: str
    evidence: list[dict[str, Any]] = field(default_factory=list)


class DynamicWorkerClient:
    """Interface for disposable VM or microVM execution.

    Dynamic execution is intentionally abstract here. Production implementations
    should use disposable VMs/microVMs, explicit network allowlists, packet
    capture, timeouts, and snapshot restoration after every run.
    """

    async def submit(self, request: DynamicWorkerRequest) -> DynamicWorkerResult:
        raise NotImplementedError("dynamic worker backend is not configured")
