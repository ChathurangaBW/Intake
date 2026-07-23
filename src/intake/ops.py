from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from intake.models import (
    Approval,
    Artifact,
    AuditLog,
    Engagement,
    Evidence,
    ExecutionJob,
    Finding,
    FindingEvidence,
    ModelCall,
    PolicyDecisionRecord,
    Target,
    ToolCall,
)
from intake.services import IntakeService, NotFoundError

EXPORT_SCHEMA_VERSION = "intake.export.v1"


def utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _dt(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def payload_sha256(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def target_record(row: Target) -> dict[str, Any]:
    return {
        "id": row.id,
        "engagement_id": row.engagement_id,
        "target_ref": row.target_ref,
        "target_type": row.target_type,
        "metadata": row.metadata_,
        "created_at": _dt(row.created_at),
        "updated_at": _dt(row.updated_at),
    }


def artifact_record(row: Artifact) -> dict[str, Any]:
    return {
        "id": row.id,
        "engagement_id": row.engagement_id,
        "sha256": row.sha256,
        "media_type": row.media_type,
        "size_bytes": row.size_bytes,
        "storage_uri": row.storage_uri,
        "source": row.source,
        "metadata": row.metadata_,
        "created_at": _dt(row.created_at),
        "updated_at": _dt(row.updated_at),
    }


def tool_call_record(row: ToolCall) -> dict[str, Any]:
    return {
        "id": row.id,
        "engagement_id": row.engagement_id,
        "actor": row.actor,
        "tool": row.tool,
        "operation": row.operation,
        "risk": row.risk,
        "request_json": row.request_json,
        "status": row.status,
        "worker_id": row.worker_id,
        "created_at": _dt(row.created_at),
        "updated_at": _dt(row.updated_at),
    }


def job_record(row: ExecutionJob) -> dict[str, Any]:
    return {
        "id": row.id,
        "tool_call_id": row.tool_call_id,
        "status": row.status,
        "priority": row.priority,
        "attempts": row.attempts,
        "max_attempts": row.max_attempts,
        "leased_by": row.leased_by,
        "leased_until": _dt(row.leased_until),
        "started_at": _dt(row.started_at),
        "finished_at": _dt(row.finished_at),
        "cancel_requested": row.cancel_requested,
        "result_json": row.result_json,
        "error": row.error,
        "created_at": _dt(row.created_at),
        "updated_at": _dt(row.updated_at),
    }


def policy_record(row: PolicyDecisionRecord) -> dict[str, Any]:
    return {
        "id": row.id,
        "tool_call_id": row.tool_call_id,
        "decision": row.decision,
        "approval_required": row.approval_required,
        "reason": row.reason,
        "raw_response": row.raw_response,
        "created_at": _dt(row.created_at),
        "updated_at": _dt(row.updated_at),
    }


def approval_record(row: Approval) -> dict[str, Any]:
    return {
        "id": row.id,
        "tool_call_id": row.tool_call_id,
        "status": row.status,
        "requested_by": row.requested_by,
        "decided_by": row.decided_by,
        "decided_at": _dt(row.decided_at),
        "reason": row.reason,
        "created_at": _dt(row.created_at),
        "updated_at": _dt(row.updated_at),
    }


def evidence_record(row: Evidence) -> dict[str, Any]:
    return {
        "id": row.id,
        "engagement_id": row.engagement_id,
        "tool_call_id": row.tool_call_id,
        "sha256": row.sha256,
        "media_type": row.media_type,
        "size_bytes": row.size_bytes,
        "storage_uri": row.storage_uri,
        "summary": row.summary,
        "metadata": row.metadata_,
        "created_at": _dt(row.created_at),
        "updated_at": _dt(row.updated_at),
    }


def finding_record(row: Finding) -> dict[str, Any]:
    return {
        "id": row.id,
        "engagement_id": row.engagement_id,
        "title": row.title,
        "severity": row.severity,
        "status": row.status,
        "description": row.description,
        "verification_status": row.verification_status,
        "created_at": _dt(row.created_at),
        "updated_at": _dt(row.updated_at),
    }


def finding_evidence_record(row: FindingEvidence) -> dict[str, Any]:
    return {
        "id": row.id,
        "finding_id": row.finding_id,
        "evidence_id": row.evidence_id,
        "relevance": row.relevance,
        "created_at": _dt(row.created_at),
        "updated_at": _dt(row.updated_at),
    }


def model_call_record(row: ModelCall) -> dict[str, Any]:
    return {
        "id": row.id,
        "engagement_id": row.engagement_id,
        "provider": row.provider,
        "model": row.model,
        "purpose": row.purpose,
        "input_tokens": row.input_tokens,
        "output_tokens": row.output_tokens,
        "cost_usd_micros": row.cost_usd_micros,
        "created_at": _dt(row.created_at),
        "updated_at": _dt(row.updated_at),
    }


def audit_record(row: AuditLog) -> dict[str, Any]:
    return {
        "id": row.id,
        "timestamp": _dt(row.timestamp),
        "actor": row.actor,
        "action": row.action,
        "subject": row.subject,
        "outcome": row.outcome,
        "metadata": row.metadata_,
    }


def readiness_report(session: Session) -> dict[str, Any]:
    counts = {
        "engagements": session.scalar(select(func.count()).select_from(Engagement)) or 0,
        "targets": session.scalar(select(func.count()).select_from(Target)) or 0,
        "artifacts": session.scalar(select(func.count()).select_from(Artifact)) or 0,
        "tool_calls": session.scalar(select(func.count()).select_from(ToolCall)) or 0,
        "execution_jobs": session.scalar(select(func.count()).select_from(ExecutionJob)) or 0,
        "pending_approvals": session.scalar(select(func.count()).select_from(Approval).where(Approval.status == "pending")) or 0,
        "evidence": session.scalar(select(func.count()).select_from(Evidence)) or 0,
        "findings": session.scalar(select(func.count()).select_from(Finding)) or 0,
        "audit_logs": session.scalar(select(func.count()).select_from(AuditLog)) or 0,
    }
    failing_conditions: list[str] = []
    if counts["pending_approvals"] > 0:
        failing_conditions.append("pending approvals require review")
    errored_jobs = session.scalar(select(func.count()).select_from(ExecutionJob).where(ExecutionJob.status == "failed")) or 0
    if errored_jobs:
        failing_conditions.append(f"{errored_jobs} execution job(s) failed")
    return {
        "status": "degraded" if failing_conditions else "ready",
        "generated_at": utc_timestamp(),
        "database": "reachable",
        "counts": counts,
        "checks": {
            "pending_approvals_clear": counts["pending_approvals"] == 0,
            "failed_jobs_clear": errored_jobs == 0,
            "audit_logging_active": counts["audit_logs"] >= 0,
        },
        "findings": failing_conditions,
    }


def engagement_export_bundle(session: Session, engagement_id: str) -> dict[str, Any]:
    engagement = session.get(Engagement, engagement_id)
    if engagement is None:
        raise NotFoundError(f"engagement not found: {engagement_id}")

    tool_calls = session.scalars(select(ToolCall).where(ToolCall.engagement_id == engagement_id)).all()
    tool_call_ids = [row.id for row in tool_calls]
    findings = session.scalars(select(Finding).where(Finding.engagement_id == engagement_id)).all()
    finding_ids = [row.id for row in findings]

    data: dict[str, Any] = {
        "engagement": {
            "id": engagement.id,
            "name": engagement.name,
            "status": engagement.status,
            "classification": engagement.classification,
            "manifest": engagement.manifest,
            "created_at": _dt(engagement.created_at),
            "updated_at": _dt(engagement.updated_at),
        },
        "targets": [target_record(row) for row in session.scalars(select(Target).where(Target.engagement_id == engagement_id)).all()],
        "artifacts": [artifact_record(row) for row in session.scalars(select(Artifact).where(Artifact.engagement_id == engagement_id)).all()],
        "tool_calls": [tool_call_record(row) for row in tool_calls],
        "execution_jobs": [
            job_record(row)
            for row in session.scalars(select(ExecutionJob).where(ExecutionJob.tool_call_id.in_(tool_call_ids))).all()
        ]
        if tool_call_ids
        else [],
        "policy_decisions": [
            policy_record(row)
            for row in session.scalars(select(PolicyDecisionRecord).where(PolicyDecisionRecord.tool_call_id.in_(tool_call_ids))).all()
        ]
        if tool_call_ids
        else [],
        "approvals": [
            approval_record(row)
            for row in session.scalars(select(Approval).where(Approval.tool_call_id.in_(tool_call_ids))).all()
        ]
        if tool_call_ids
        else [],
        "evidence": [evidence_record(row) for row in session.scalars(select(Evidence).where(Evidence.engagement_id == engagement_id)).all()],
        "findings": [finding_record(row) for row in findings],
        "finding_evidence": [
            finding_evidence_record(row)
            for row in session.scalars(select(FindingEvidence).where(FindingEvidence.finding_id.in_(finding_ids))).all()
        ]
        if finding_ids
        else [],
        "model_calls": [model_call_record(row) for row in session.scalars(select(ModelCall).where(ModelCall.engagement_id == engagement_id)).all()],
    }
    manifest = {
        "schema_version": EXPORT_SCHEMA_VERSION,
        "generated_at": utc_timestamp(),
        "engagement_id": engagement_id,
        "includes_evidence_bytes": False,
        "record_counts": {key: len(value) for key, value in data.items() if isinstance(value, list)},
    }
    bundle = {"manifest": manifest, "data": data}
    bundle["manifest"]["sha256"] = payload_sha256(bundle["data"])
    return bundle


def audit_ndjson(session: Session, limit: int = 1000) -> str:
    rows = session.scalars(select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit)).all()
    return "\n".join(_canonical_json(audit_record(row)) for row in rows) + ("\n" if rows else "")


def verify_evidence_inventory(session: Session, limit: int = 500) -> dict[str, Any]:
    service = IntakeService(session)
    rows = session.scalars(select(Evidence).order_by(Evidence.created_at.desc()).limit(limit)).all()
    checked: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for row in rows:
        try:
            evidence, data = service.get_evidence_bytes(row.id)
            actual = hashlib.sha256(data).hexdigest()
            ok = actual == evidence.sha256 and len(data) == evidence.size_bytes
            item = {
                "evidence_id": row.id,
                "expected_sha256": evidence.sha256,
                "actual_sha256": actual,
                "expected_size_bytes": evidence.size_bytes,
                "actual_size_bytes": len(data),
                "valid": ok,
            }
        except Exception as error:  # noqa: BLE001 - inventory must continue
            item = {"evidence_id": row.id, "valid": False, "error": str(error)}
            ok = False
        checked.append(item)
        if not ok:
            failures.append(item)
    return {
        "status": "failed" if failures else "ok",
        "generated_at": utc_timestamp(),
        "checked": len(checked),
        "failures": failures,
        "results": checked,
    }
