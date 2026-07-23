from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from intake.schemas import ToolCallDecision


class EngagementCreate(BaseModel):
    engagement_id: str
    name: str
    classification: str = "internal"
    manifest: dict[str, Any] = Field(default_factory=dict)


class EngagementOut(BaseModel):
    id: str
    name: str
    status: str
    classification: str
    manifest: dict[str, Any]


class TargetCreate(BaseModel):
    target_ref: str
    target_type: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class TargetOut(BaseModel):
    id: str
    engagement_id: str
    target_ref: str
    target_type: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ArtifactOut(BaseModel):
    id: str
    engagement_id: str
    sha256: str
    media_type: str
    size_bytes: int
    storage_uri: str
    source: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ToolCallOut(BaseModel):
    id: str
    engagement_id: str
    actor: str
    tool: str
    operation: str
    risk: str
    status: str
    request_json: dict[str, Any]


class ToolCallProposeOut(BaseModel):
    tool_call_id: str
    status: str
    approval_id: str | None = None
    decision: ToolCallDecision


class ToolExecutionOut(BaseModel):
    status: str
    summary: str
    evidence_ids: list[str] = Field(default_factory=list)
    data: dict[str, Any] = Field(default_factory=dict)


class ApprovalDecision(BaseModel):
    approved: bool
    decided_by: str
    reason: str | None = None


class ApprovalOut(BaseModel):
    id: str
    tool_call_id: str
    status: str
    requested_by: str
    decided_by: str | None = None
    reason: str | None = None


class EvidenceCreate(BaseModel):
    data: str = Field(description="UTF-8 text payload to store as evidence")
    media_type: str = "text/plain"
    summary: str | None = None
    tool_call_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvidenceOut(BaseModel):
    id: str
    engagement_id: str
    sha256: str
    media_type: str
    size_bytes: int
    storage_uri: str
    summary: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class FindingCreate(BaseModel):
    title: str
    description: str
    severity: str = "informational"
    evidence_ids: list[str] = Field(default_factory=list)


class FindingOut(BaseModel):
    id: str
    engagement_id: str
    title: str
    severity: str
    status: str
    verification_status: str
    description: str


def engagement_out(row: Any) -> EngagementOut:
    return EngagementOut(
        id=row.id,
        name=row.name,
        status=row.status,
        classification=row.classification,
        manifest=row.manifest,
    )


def target_out(row: Any) -> TargetOut:
    return TargetOut(
        id=row.id,
        engagement_id=row.engagement_id,
        target_ref=row.target_ref,
        target_type=row.target_type,
        metadata=row.metadata_,
    )


def artifact_out(row: Any) -> ArtifactOut:
    return ArtifactOut(
        id=row.id,
        engagement_id=row.engagement_id,
        sha256=row.sha256,
        media_type=row.media_type,
        size_bytes=row.size_bytes,
        storage_uri=row.storage_uri,
        source=row.source,
        metadata=row.metadata_,
    )


def tool_call_out(row: Any) -> ToolCallOut:
    return ToolCallOut(
        id=row.id,
        engagement_id=row.engagement_id,
        actor=row.actor,
        tool=row.tool,
        operation=row.operation,
        risk=row.risk,
        status=row.status,
        request_json=row.request_json,
    )


def approval_out(row: Any) -> ApprovalOut:
    return ApprovalOut(
        id=row.id,
        tool_call_id=row.tool_call_id,
        status=row.status,
        requested_by=row.requested_by,
        decided_by=row.decided_by,
        reason=row.reason,
    )


def evidence_out(row: Any) -> EvidenceOut:
    return EvidenceOut(
        id=row.id,
        engagement_id=row.engagement_id,
        sha256=row.sha256,
        media_type=row.media_type,
        size_bytes=row.size_bytes,
        storage_uri=row.storage_uri,
        summary=row.summary,
        metadata=row.metadata_,
    )


def finding_out(row: Any) -> FindingOut:
    return FindingOut(
        id=row.id,
        engagement_id=row.engagement_id,
        title=row.title,
        severity=row.severity,
        status=row.status,
        verification_status=row.verification_status,
        description=row.description,
    )
