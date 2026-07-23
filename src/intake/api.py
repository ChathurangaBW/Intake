from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends, FastAPI, HTTPException, Response, status
from sqlalchemy.orm import Session

from intake.db import get_session
from intake.reporting import render_markdown_report
from intake.runtime_schemas import (
    ApprovalDecision,
    ApprovalOut,
    ArtifactOut,
    EngagementCreate,
    EngagementOut,
    EvidenceCreate,
    EvidenceOut,
    FindingCreate,
    FindingOut,
    TargetCreate,
    TargetOut,
    ToolCallOut,
    ToolCallProposeOut,
    approval_out,
    artifact_out,
    engagement_out,
    evidence_out,
    finding_out,
    target_out,
    tool_call_out,
)
from intake.schemas import ToolCallDecision, ToolCallRequest
from intake.services import IntakeError, IntakeService, NotFoundError, ScopeError

app = FastAPI(title="Intake", version="0.2.0")


def session_dep() -> Generator[Session, None, None]:
    yield from get_session()


def service_dep(session: Session = Depends(session_dep)) -> IntakeService:
    return IntakeService(session)


def handle_error(error: Exception) -> HTTPException:
    if isinstance(error, NotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
    if isinstance(error, ScopeError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error))
    if isinstance(error, IntakeError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="internal error")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/engagements", response_model=EngagementOut, status_code=status.HTTP_201_CREATED)
def create_engagement(payload: EngagementCreate, service: IntakeService = Depends(service_dep)) -> EngagementOut:
    try:
        row = service.create_engagement(
            engagement_id=payload.engagement_id,
            name=payload.name,
            classification=payload.classification,
            manifest=payload.manifest,
        )
        return engagement_out(row)
    except Exception as error:  # noqa: BLE001 - translated to HTTP boundary
        raise handle_error(error) from error


@app.get("/engagements", response_model=list[EngagementOut])
def list_engagements(service: IntakeService = Depends(service_dep)) -> list[EngagementOut]:
    return [engagement_out(row) for row in service.list_engagements()]


@app.get("/engagements/{engagement_id}", response_model=EngagementOut)
def get_engagement(engagement_id: str, service: IntakeService = Depends(service_dep)) -> EngagementOut:
    try:
        return engagement_out(service.get_engagement(engagement_id))
    except Exception as error:  # noqa: BLE001
        raise handle_error(error) from error


@app.post("/engagements/{engagement_id}/targets", response_model=TargetOut, status_code=status.HTTP_201_CREATED)
def add_target(
    engagement_id: str,
    payload: TargetCreate,
    service: IntakeService = Depends(service_dep),
) -> TargetOut:
    try:
        row = service.add_target(
            engagement_id=engagement_id,
            target_ref=payload.target_ref,
            target_type=payload.target_type,
            metadata=payload.metadata,
        )
        return target_out(row)
    except Exception as error:  # noqa: BLE001
        raise handle_error(error) from error


@app.get("/engagements/{engagement_id}/targets", response_model=list[TargetOut])
def list_targets(engagement_id: str, service: IntakeService = Depends(service_dep)) -> list[TargetOut]:
    try:
        return [target_out(row) for row in service.list_targets(engagement_id)]
    except Exception as error:  # noqa: BLE001
        raise handle_error(error) from error


@app.get("/engagements/{engagement_id}/artifacts", response_model=list[ArtifactOut])
def list_artifacts(engagement_id: str, service: IntakeService = Depends(service_dep)) -> list[ArtifactOut]:
    try:
        return [artifact_out(row) for row in service.list_artifacts(engagement_id)]
    except Exception as error:  # noqa: BLE001
        raise handle_error(error) from error


@app.post("/authorize", response_model=ToolCallDecision)
async def authorize_tool_call(request: ToolCallRequest, service: IntakeService = Depends(service_dep)) -> ToolCallDecision:
    try:
        result = await service.propose_tool_call(request)
        return result.decision
    except Exception as error:  # noqa: BLE001
        raise handle_error(error) from error


@app.post("/tool-calls", response_model=ToolCallProposeOut, status_code=status.HTTP_201_CREATED)
async def propose_tool_call(
    request: ToolCallRequest,
    service: IntakeService = Depends(service_dep),
) -> ToolCallProposeOut:
    try:
        result = await service.propose_tool_call(request)
        return ToolCallProposeOut(
            tool_call_id=result.tool_call_id,
            status=result.status,
            approval_id=result.approval_id,
            decision=result.decision,
        )
    except Exception as error:  # noqa: BLE001
        raise handle_error(error) from error


@app.get("/engagements/{engagement_id}/tool-calls", response_model=list[ToolCallOut])
def list_tool_calls(engagement_id: str, service: IntakeService = Depends(service_dep)) -> list[ToolCallOut]:
    try:
        return [tool_call_out(row) for row in service.list_tool_calls(engagement_id)]
    except Exception as error:  # noqa: BLE001
        raise handle_error(error) from error


@app.post("/approvals/{approval_id}/decision", response_model=ApprovalOut)
def decide_approval(
    approval_id: str,
    payload: ApprovalDecision,
    service: IntakeService = Depends(service_dep),
) -> ApprovalOut:
    try:
        row = service.decide_approval(
            approval_id,
            approved=payload.approved,
            decided_by=payload.decided_by,
            reason=payload.reason,
        )
        return approval_out(row)
    except Exception as error:  # noqa: BLE001
        raise handle_error(error) from error


@app.post("/engagements/{engagement_id}/evidence", response_model=EvidenceOut, status_code=status.HTTP_201_CREATED)
def record_evidence(
    engagement_id: str,
    payload: EvidenceCreate,
    service: IntakeService = Depends(service_dep),
) -> EvidenceOut:
    try:
        row = service.record_evidence(
            engagement_id=engagement_id,
            data=payload.data.encode("utf-8"),
            media_type=payload.media_type,
            summary=payload.summary,
            tool_call_id=payload.tool_call_id,
            metadata=payload.metadata,
        )
        return evidence_out(row)
    except Exception as error:  # noqa: BLE001
        raise handle_error(error) from error


@app.post("/engagements/{engagement_id}/findings", response_model=FindingOut, status_code=status.HTTP_201_CREATED)
def create_finding(
    engagement_id: str,
    payload: FindingCreate,
    service: IntakeService = Depends(service_dep),
) -> FindingOut:
    try:
        row = service.create_finding(
            engagement_id=engagement_id,
            title=payload.title,
            description=payload.description,
            severity=payload.severity,
            evidence_ids=payload.evidence_ids,
        )
        return finding_out(row)
    except Exception as error:  # noqa: BLE001
        raise handle_error(error) from error


@app.get("/engagements/{engagement_id}/findings", response_model=list[FindingOut])
def list_findings(engagement_id: str, service: IntakeService = Depends(service_dep)) -> list[FindingOut]:
    try:
        return [finding_out(row) for row in service.list_findings(engagement_id)]
    except Exception as error:  # noqa: BLE001
        raise handle_error(error) from error


@app.get("/engagements/{engagement_id}/report.md")
def report_markdown(engagement_id: str, service: IntakeService = Depends(service_dep)) -> Response:
    try:
        engagement = service.get_engagement(engagement_id)
        findings = service.list_findings(engagement_id)
        body = render_markdown_report(engagement=engagement, findings=findings)
        return Response(content=body, media_type="text/markdown")
    except Exception as error:  # noqa: BLE001
        raise handle_error(error) from error
