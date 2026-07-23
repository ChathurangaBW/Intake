from __future__ import annotations

from intake.policy import PolicyClient
from intake.schemas import PolicyDecision, ToolCallRequest
from intake.tools.base import ToolResult
from intake.tools.registry import ToolRegistry


class ToolBroker:
    """The only path from a proposed agent action to a tool implementation."""

    def __init__(self, *, registry: ToolRegistry, policy_client: PolicyClient | None = None) -> None:
        self.registry = registry
        self.policy_client = policy_client or PolicyClient()

    async def execute(self, request: ToolCallRequest) -> ToolResult:
        decision = await self.policy_client.decide(request)
        if decision.decision == PolicyDecision.DENY:
            return ToolResult(status="denied", summary=decision.reason or "policy denied tool call")
        if decision.decision == PolicyDecision.QUARANTINE:
            return ToolResult(status="quarantined", summary=decision.reason or "policy quarantined tool call")
        if decision.approval_required or decision.decision == PolicyDecision.APPROVE:
            return ToolResult(status="approval_required", summary=decision.reason or "human review required")

        tool = self.registry.get(request.tool, request.operation)
        return await tool.run(request.arguments)
