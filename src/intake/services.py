from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from intake.config import settings
from intake.models import (
    Approval,
    Artifact,
    AuditLog,
    Engagement,
    Evidence,
    Finding,
    FindingEvidence,
    ModelCall,
    PolicyDecisionRecord,
    Target,
    ToolCall,
    utcnow,
)
from intake.policy import PolicyClient
from intake.schemas import PolicyDecision, ToolCallDecision, ToolCallRequest
from intake.storage import EvidenceStore
from intake.tool_runtime import build_default_registry
from intake.tools.base import ToolResult


class IntakeError(RuntimeError):
    """Base application error."""


class NotFoundError(IntakeError):
    """Raised when a requested record cannot be found."""


class ScopeError(IntakeError):
    """Raised when a request is outside the engagement scope."""


@dataclass(frozen=True)
class ToolCallResult:
    tool_call_id: str
    decision: ToolCallDecision
    status: str
    approval_id: str | None = None


class IntakeService:
    """Runtime service layer for the Intake API and CLI."""

    def __init__(
        self,
        session: Session,
        *,
        policy_client: PolicyClient | None = None,
        evidence_store: EvidenceStore | None = None,
    ) -> None:
        self.session = session
        self.policy_client = policy_client or PolicyClient()
        self._evidence_store = evidence_store

    @property
    def evidence_store(self) -> EvidenceStore:
        if self._evidence_store is None:
            self._evidence_store = EvidenceStore()
        return self._evidence_store

    def audit(
        self,
        *,
        actor: str,
        action: str,
        subject: str,
        outcome: str,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        event = AuditLog(
            actor=actor,
            action=action,
            subject=subject,
            outcome=outcome,
            metadata_=metadata or {},
        )
        self.session.add(event)
        self.session.flush()
        return event

    def dashboard_stats(self) -> dict[str, int]:
        return {
            "engagements": self._count(Engagement),
            "targets": self._count(Target),
            "artifacts": self._count(Artifact),
            "evidence": self._count(Evidence),
            "tool_calls": self._count(ToolCall),
            "approvals_pending": self._count(Approval, Approval.status == "pending"),
            "findings": self._count(Finding),
        }

    def _count(self, model: type[object], *conditions: object) -> int:
        stmt = select(func.count()).select_from(model)
        for condition in conditions:
            stmt = stmt.where(condition)
        return int(self.session.scalar(stmt) or 0)

    def create_engagement(
        self,
        *,
        engagement_id: str,
        name: str,
        classification: str = "internal",
        manifest: dict[str, Any] | None = None,
        actor: str = "operator",
    ) -> Engagement:
        existing = self.session.get(Engagement, engagement_id)
        if existing is not None:
            raise IntakeError(f"engagement already exists: {engagement_id}")
        engagement = Engagement(
            id=engagement_id,
            name=name,
            classification=classification,
            manifest=manifest or {},
            status="active",
        )
        self.session.add(engagement)
        self.audit(actor=actor, action="engagement.create", subject=engagement_id, outcome="success")
        self.session.commit()
        self.session.refresh(engagement)
        return engagement

    def get_engagement(self, engagement_id: str) -> Engagement:
        engagement = self.session.get(Engagement, engagement_id)
        if engagement is None:
            raise NotFoundError(f"unknown engagement: {engagement_id}")
        return engagement

    def list_engagements(self) -> list[Engagement]:
        return list(self.session.scalars(select(Engagement).order_by(Engagement.created_at.desc())))

    def add_target(
        self,
        *,
        engagement_id: str,
        target_ref: str,
        target_type: str,
        metadata: dict[str, Any] | None = None,
        actor: str = "operator",
    ) -> Target:
        self.get_engagement(engagement_id)
        target = Target(
            engagement_id=engagement_id,
            target_ref=target_ref,
            target_type=target_type,
            metadata_=metadata or {},
        )
        self.session.add(target)
        self.audit(
            actor=actor,
            action="target.add",
            subject=f"{engagement_id}:{target_ref}",
            outcome="success",
            metadata={"target_type": target_type},
        )
        self.session.commit()
        self.session.refresh(target)
        return target

    def list_targets(self, engagement_id: str) -> list[Target]:
        self.get_engagement(engagement_id)
        stmt = select(Target).where(Target.engagement_id == engagement_id).order_by(Target.created_at)
        return list(self.session.scalars(stmt))

    def _create_artifact_record(
        self,
        *,
        engagement_id: str,
        sha256: str,
        media_type: str,
        size_bytes: int,
        storage_uri: str,
        source: str,
        metadata: dict[str, Any] | None = None,
        actor: str = "operator",
    ) -> Artifact:
        artifact = Artifact(
            engagement_id=engagement_id,
            sha256=sha256,
            media_type=media_type,
            size_bytes=size_bytes,
            storage_uri=storage_uri,
            source=source,
            metadata_=metadata or {},
        )
        self.session.add(artifact)
        self.session.flush()
        self.audit(
            actor=actor,
            action="artifact.ingest",
            subject=f"{engagement_id}:{artifact.id}",
            outcome="success",
            metadata={"sha256": sha256, "size_bytes": size_bytes, "source": source},
        )
        self.session.commit()
        self.session.refresh(artifact)
        return artifact

    def ingest_artifact(
        self,
        *,
        engagement_id: str,
        path: str | Path,
        media_type: str = "application/octet-stream",
        source: str = "manual",
        metadata: dict[str, Any] | None = None,
        actor: str = "operator",
    ) -> Artifact:
        self.get_engagement(engagement_id)
        stored = self.evidence_store.put_file(path, media_type=media_type)
        return self._create_artifact_record(
            engagement_id=engagement_id,
            sha256=stored.sha256,
            media_type=media_type,
            size_bytes=stored.size_bytes,
            storage_uri=stored.storage_uri,
            source=source,
            metadata=metadata,
            actor=actor,
        )

    def ingest_artifact_bytes(
        self,
        *,
        engagement_id: str,
        data: bytes,
        media_type: str = "application/octet-stream",
        source: str = "api-upload",
        metadata: dict[str, Any] | None = None,
        actor: str = "operator",
    ) -> Artifact:
        self.get_engagement(engagement_id)
        stored = self.evidence_store.put_bytes(data, media_type=media_type)
        return self._create_artifact_record(
            engagement_id=engagement_id,
            sha256=stored.sha256,
            media_type=media_type,
            size_bytes=stored.size_bytes,
            storage_uri=stored.storage_uri,
            source=source,
            metadata=metadata,
            actor=actor,
        )

    def get_artifact(self, artifact_id: str) -> Artifact:
        artifact = self.session.get(Artifact, artifact_id)
        if artifact is None:
            raise NotFoundError(f"unknown artifact: {artifact_id}")
        return artifact

    def list_artifacts(self, engagement_id: str) -> list[Artifact]:
        self.get_engagement(engagement_id)
        stmt = select(Artifact).where(Artifact.engagement_id == engagement_id).order_by(Artifact.created_at.desc())
        return list(self.session.scalars(stmt))

    async def propose_tool_call(self, request: ToolCallRequest) -> ToolCallResult:
        self.get_engagement(request.engagement_id)
        tool_call = ToolCall(
            engagement_id=request.engagement_id,
            actor=request.actor,
            tool=request.tool,
            operation=request.operation,
            risk=request.risk.value,
            request_json=request.model_dump(mode="json"),
            status="proposed",
        )
        self.session.add(tool_call)
        self.session.flush()

        decision = await self.policy_client.decide(request)
        decision_record = PolicyDecisionRecord(
            tool_call_id=tool_call.id,
            decision=decision.decision.value,
            approval_required=decision.approval_required,
            reason=decision.reason,
            raw_response=decision.model_dump(mode="json"),
        )
        self.session.add(decision_record)

        approval_id: str | None = None
        if decision.decision == PolicyDecision.ALLOW and not decision.approval_required:
            tool_call.status = "authorized"
        elif decision.decision == PolicyDecision.APPROVE or decision.approval_required:
            approval = Approval(
                tool_call_id=tool_call.id,
                status="pending",
                requested_by=request.actor,
                reason=decision.reason,
            )
            self.session.add(approval)
            self.session.flush()
            approval_id = approval.id
            tool_call.status = "waiting_approval"
        else:
            tool_call.status = "denied"

        self.audit(
            actor=request.actor,
            action="tool.propose",
            subject=f"{request.engagement_id}:{tool_call.id}",
            outcome=tool_call.status,
            metadata={"tool": request.tool, "operation": request.operation, "decision": decision.decision.value},
        )
        self.session.commit()
        return ToolCallResult(
            tool_call_id=tool_call.id,
            decision=decision,
            status=tool_call.status,
            approval_id=approval_id,
        )

    def list_tool_calls(self, engagement_id: str) -> list[ToolCall]:
        self.get_engagement(engagement_id)
        stmt = select(ToolCall).where(ToolCall.engagement_id == engagement_id).order_by(ToolCall.created_at.desc())
        return list(self.session.scalars(stmt))

    def list_tools(self) -> list[dict[str, object]]:
        registry = build_default_registry(self.session)
        return registry.list_specs()

    def tool_status(self) -> list[dict[str, object]]:
        registry = build_default_registry(self.session)
        specs = registry.list_specs()
        rows: list[dict[str, object]] = []
        for spec in specs:
            name = str(spec["name"])
            available = True
            runtime = "local-static-fallback"
            detail = "Built-in metadata/string extraction fallback is available."
            if name == "rizin" and settings.enable_external_static_tools:
                available = shutil.which(settings.rizin_path) is not None
                runtime = "external-fixed-argv" if available else "fallback"
                detail = f"Rizin path: {settings.rizin_path}"
            if name == "ghidra" and settings.enable_external_static_tools:
                available = shutil.which(settings.ghidra_analyze_headless_path) is not None
                runtime = "external-fixed-argv" if available else "fallback"
                detail = f"Ghidra analyzeHeadless path: {settings.ghidra_analyze_headless_path}"
            rows.append({"name": name, "operation": spec["operation"], "available": available, "runtime": runtime, "detail": detail})
        return rows

    async def execute_tool_call(self, tool_call_id: str) -> ToolResult:
        tool_call = self.session.get(ToolCall, tool_call_id)
        if tool_call is None:
            raise NotFoundError(f"unknown tool call: {tool_call_id}")
        if tool_call.status != "authorized":
            raise IntakeError(f"tool call is not authorized: {tool_call.status}")
        request_json = dict(tool_call.request_json)
        request_json.setdefault("arguments", {})
        request_json["arguments"] = dict(request_json["arguments"])
        request_json["arguments"]["tool_call_id"] = tool_call.id
        request = ToolCallRequest.model_validate(request_json)

        registry = build_default_registry(self.session)
        tool = registry.get(request.tool, request.operation)
        result = await tool.run(request.arguments)
        tool_call.status = "completed" if result.status == "completed" else result.status
        self.audit(
            actor=tool_call.actor,
            action="tool.execute",
            subject=f"{tool_call.engagement_id}:{tool_call.id}",
            outcome=tool_call.status,
            metadata={"summary": result.summary, "evidence_ids": result.evidence_ids},
        )
        self.session.commit()
        return result

    def decide_approval(self, approval_id: str, *, approved: bool, decided_by: str, reason: str | None = None) -> Approval:
        approval = self.session.get(Approval, approval_id)
        if approval is None:
            raise NotFoundError(f"unknown approval: {approval_id}")
        approval.status = "approved" if approved else "rejected"
        approval.decided_by = decided_by
        approval.decided_at = utcnow()
        approval.reason = reason
        tool_call = self.session.get(ToolCall, approval.tool_call_id)
        if tool_call is not None:
            tool_call.status = "authorized" if approved else "rejected"
        self.audit(
            actor=decided_by,
            action="approval.decide",
            subject=approval_id,
            outcome=approval.status,
            metadata={"tool_call_id": approval.tool_call_id, "reason": reason},
        )
        self.session.commit()
        self.session.refresh(approval)
        return approval

    def list_pending_approvals(self) -> list[Approval]:
        stmt = select(Approval).where(Approval.status == "pending").order_by(Approval.created_at.desc())
        return list(self.session.scalars(stmt))

    def record_evidence(
        self,
        *,
        engagement_id: str,
        data: bytes,
        media_type: str,
        summary: str | None = None,
        tool_call_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        actor: str = "operator",
    ) -> Evidence:
        self.get_engagement(engagement_id)
        stored = self.evidence_store.put_bytes(data, media_type=media_type)
        evidence = Evidence(
            engagement_id=engagement_id,
            tool_call_id=tool_call_id,
            sha256=stored.sha256,
            media_type=media_type,
            size_bytes=stored.size_bytes,
            storage_uri=stored.storage_uri,
            summary=summary,
            metadata_=metadata or {},
        )
        self.session.add(evidence)
        self.session.flush()
        self.audit(
            actor=actor,
            action="evidence.record",
            subject=f"{engagement_id}:{evidence.id}",
            outcome="success",
            metadata={"sha256": stored.sha256, "tool_call_id": tool_call_id},
        )
        self.session.commit()
        self.session.refresh(evidence)
        return evidence

    def list_evidence(self, engagement_id: str) -> list[Evidence]:
        self.get_engagement(engagement_id)
        stmt = select(Evidence).where(Evidence.engagement_id == engagement_id).order_by(Evidence.created_at.desc())
        return list(self.session.scalars(stmt))

    def get_evidence_bytes(self, evidence_id: str) -> tuple[Evidence, bytes]:
        evidence = self.session.get(Evidence, evidence_id)
        if evidence is None:
            raise NotFoundError(f"unknown evidence: {evidence_id}")
        return evidence, self.evidence_store.get_bytes(evidence.sha256)

    def create_finding(
        self,
        *,
        engagement_id: str,
        title: str,
        description: str,
        severity: str = "informational",
        evidence_ids: list[str] | None = None,
        actor: str = "operator",
    ) -> Finding:
        self.get_engagement(engagement_id)
        finding = Finding(
            engagement_id=engagement_id,
            title=title,
            severity=severity,
            description=description,
            status="draft",
            verification_status="unverified",
        )
        self.session.add(finding)
        self.session.flush()
        for evidence_id in evidence_ids or []:
            evidence = self.session.get(Evidence, evidence_id)
            if evidence is None or evidence.engagement_id != engagement_id:
                raise ScopeError(f"evidence outside engagement: {evidence_id}")
            self.session.add(FindingEvidence(finding_id=finding.id, evidence_id=evidence_id, relevance="supporting evidence"))
        self.audit(
            actor=actor,
            action="finding.create",
            subject=f"{engagement_id}:{finding.id}",
            outcome="success",
            metadata={"severity": severity, "evidence_ids": evidence_ids or []},
        )
        self.session.commit()
        self.session.refresh(finding)
        return finding

    def list_findings(self, engagement_id: str) -> list[Finding]:
        self.get_engagement(engagement_id)
        stmt = select(Finding).where(Finding.engagement_id == engagement_id).order_by(Finding.created_at.desc())
        return list(self.session.scalars(stmt))

    def list_audit_logs(self, limit: int = 100) -> list[AuditLog]:
        stmt = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit)
        return list(self.session.scalars(stmt))

    def list_model_calls(self, engagement_id: str | None = None) -> list[ModelCall]:
        stmt = select(ModelCall).order_by(ModelCall.created_at.desc())
        if engagement_id is not None:
            stmt = stmt.where(ModelCall.engagement_id == engagement_id)
        return list(self.session.scalars(stmt))
