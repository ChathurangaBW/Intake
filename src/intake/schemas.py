from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class RiskLevel(StrEnum):
    READ_ONLY = "read_only"
    STATE_CHANGING = "state_changing"
    DYNAMIC_EXECUTION = "dynamic_execution"
    NETWORK_ACTIVE = "network_active"


class PolicyDecision(StrEnum):
    ALLOW = "allow"
    APPROVE = "approve"
    DENY = "deny"
    QUARANTINE = "quarantine"


class EngagementScope(BaseModel):
    engagement_id: str
    authorized_targets: list[str] = Field(default_factory=list)
    authorized_artifacts: list[str] = Field(default_factory=list)
    denied_operations: list[str] = Field(default_factory=list)


class ToolCallRequest(BaseModel):
    engagement_id: str
    actor: str
    tool: str
    operation: str
    risk: RiskLevel
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolCallDecision(BaseModel):
    decision: PolicyDecision
    approval_required: bool = False
    maximum_runtime_seconds: int = 300
    network_policy: Literal["deny_all", "target_allowlist", "internet"] = "deny_all"
    reason: str | None = None


class EvidenceRecord(BaseModel):
    evidence_id: str
    sha256: str
    media_type: str
    size_bytes: int
    source_tool: str
    metadata: dict[str, Any] = Field(default_factory=dict)
