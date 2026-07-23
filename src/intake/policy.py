import httpx

from intake.config import settings
from intake.schemas import PolicyDecision, ToolCallDecision, ToolCallRequest


class PolicyClient:
    """Client for the policy boundary.

    The model or planner may propose a tool call, but this client must decide
    whether that call is allowed before any worker receives it.
    """

    def __init__(self, opa_url: str | None = None) -> None:
        self.opa_url = opa_url or settings.opa_url

    async def decide(self, request: ToolCallRequest) -> ToolCallDecision:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(self.opa_url, json={"input": request.model_dump(mode="json")})
            response.raise_for_status()
            payload = response.json().get("result") or {}

        decision = payload.get("decision", PolicyDecision.DENY.value)
        return ToolCallDecision(
            decision=PolicyDecision(decision),
            approval_required=bool(payload.get("approval_required", decision == "approve")),
            maximum_runtime_seconds=int(payload.get("maximum_runtime_seconds", 300)),
            network_policy=payload.get("network_policy", "deny_all"),
            reason=payload.get("reason"),
        )
