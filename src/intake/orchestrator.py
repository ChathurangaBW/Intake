from intake.policy import PolicyClient
from intake.schemas import PolicyDecision, ToolCallDecision, ToolCallRequest


class Orchestrator:
    """Minimal policy-gated execution orchestrator.

    This class intentionally does not expose generic shell execution. Add typed
    tools under ``intake.tools`` and route them through this boundary.
    """

    def __init__(self, policy_client: PolicyClient | None = None) -> None:
        self.policy_client = policy_client or PolicyClient()

    async def authorize(self, request: ToolCallRequest) -> ToolCallDecision:
        decision = await self.policy_client.decide(request)
        if decision.decision in {PolicyDecision.DENY, PolicyDecision.QUARANTINE}:
            return decision
        return decision
