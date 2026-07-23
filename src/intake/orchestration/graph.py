from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from intake.schemas import ToolCallRequest
from intake.tool_broker import ToolBroker
from intake.tools.base import ToolResult


class WorkflowPhase(StrEnum):
    INTAKE = "intake"
    SCOPE_VALIDATION = "scope_validation"
    PLANNING = "planning"
    POLICY_REVIEW = "policy_review"
    EXECUTION = "execution"
    EVIDENCE_REVIEW = "evidence_review"
    VERIFICATION = "verification"
    REPORTING = "reporting"
    COMPLETE = "complete"


@dataclass
class WorkflowState:
    engagement_id: str
    objective: str
    phase: WorkflowPhase = WorkflowPhase.INTAKE
    plan: list[dict[str, Any]] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    findings: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class IntakeWorkflow:
    """Small deterministic skeleton intended to be replaced by LangGraph nodes.

    The important boundary is preserved here: plans produce typed tool call
    requests, and only the broker can execute them after policy review.
    """

    def __init__(self, broker: ToolBroker) -> None:
        self.broker = broker

    async def execute_step(self, state: WorkflowState, request: ToolCallRequest) -> ToolResult:
        state.phase = WorkflowPhase.POLICY_REVIEW
        result = await self.broker.execute(request)
        if result.status == "ok":
            state.evidence_ids.extend(result.evidence_ids)
            state.phase = WorkflowPhase.EVIDENCE_REVIEW
        elif result.status in {"denied", "quarantined", "approval_required"}:
            state.errors.append(result.summary)
            state.phase = WorkflowPhase.POLICY_REVIEW
        else:
            state.phase = WorkflowPhase.EXECUTION
        return result
