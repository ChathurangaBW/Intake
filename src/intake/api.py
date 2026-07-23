from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, Response, UploadFile, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from intake import __version__
from intake.auth import install_api_key_auth, principal_from_request
from intake.config import settings
from intake.db import get_session
from intake.ops_api import router as ops_router
from intake.platform import install_platform, router as platform_router
from intake.release_api import router as release_router
from intake.reporting import render_markdown_report
from intake.runtime_schemas import (
    ApprovalDecision,
    ApprovalOut,
    ArtifactOut,
    AuditLogOut,
    DashboardStats,
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
    ToolExecutionOut,
    ToolSpecOut,
    ToolStatusOut,
    approval_out,
    artifact_out,
    audit_log_out,
    engagement_out,
    evidence_out,
    finding_out,
    target_out,
    tool_call_out,
)
from intake.schemas import ToolCallDecision, ToolCallRequest
from intake.services import IntakeError, IntakeService, NotFoundError, ScopeError
from intake.web import render_dashboard, render_engagement

app = FastAPI(
    title="Intake",
    version=__version__,
    description="Policy-gated security automation for authorized assessment workflows.",
)
install_api_key_auth(app)
install_platform(app)
app.include_router(platform_router)
app.include_router(release_router)
app.include_router(ops_router)


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


def actor_for(request: Request, fallback: str = "api") -> str:
    principal = principal_from_request(request)
    if principal.key_id == "local-development":
        return fallback
    return principal.key_id


@app.get("/health", tags=["platform"])
def health() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "auth_enabled": bool(settings.api_key or settings.api_keys),
        "version": app.version,
    }


@app.get("/ui", response_class=HTMLResponse, tags=["ui"])
def ui_dashboard(session: Session = Depends(session_dep)) -> HTMLResponse:
    if not settings.enable_web_ui:
        raise HTTPException(status_code=404, detail="web UI is disabled")
    return HTMLResponse(render_dashboard(session))


@app.get("/ui/engagements/{engagement_id}", response_class=HTMLResponse, tags=["ui"])
def ui_engagement(engagement_id: str, session: Session = Depends(session_dep)) -> HTMLResponse:
    if not settings.enable_web_ui:
        raise HTTPException(status_code=404, detail="web UI is disabled")
    return HTMLResponse(render_engagement(session, engagement_id))


@app.get("/stats", response_model=DashboardStats, tags=["platform"])
def dashboard_stats(service: IntakeService = Depends(service_dep)) -> DashboardStats:
    return DashboardStats(**service.dashboard_stats())


@app.post("/engagements", response_model=EngagementOut, status_code=status.HTTP_201_CREATED, tags=["engagements"])
def create_engagement(
    payload: EngagementCreate,
    request: Request,
    service: IntakeService = Depends(service_dep),
) -> EngagementOut:
    try:
        row = service.create_engagement(
            engagement_id=payload.engagement_id,
            name=payload.name,
            classification=payload.classification,
            manifest=payload.manifest,
            actor=actor_for(request),
        )
        return engagement_out(row)
    except Exception as error:  # noqa: BLE001
        raise handle_error(error) from error


@app.get("/engagements", response_model=list[EngagementOut], tags=["engagements"])
def list_engagements(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    service: IntakeService = Depends(service_dep),
) -> list[EngagementOut]:
    return [engagement_out(row) for row in service.list_engagements()[offset : offset + limit]]


@app.get("/engagements/{engagement_id}", response_model=EngagementOut, tags=["engagements"])
def get_engagement(engagement_id: str, service: IntakeService = Depends(service_dep)) -> EngagementOut:
    try:
        return engagement_out(service.get_engagement(engagement_id))
    except Exception as error:  # noqa: BLE001
        raise handle_error(error) from error


@app.post(
    "/engagements/{engagement_id}/targets",
    response_model=TargetOut,
    status_code=status.HTTP_201_CREATED,
    tags=["targets"],
)
def add_target(
    engagement_id: str,
    payload: TargetCreate,
    request: Request,
    service: IntakeService = Depends(service_dep),
) -> TargetOut:
    try:
        row = service.add_target(
            engagement_id=engagement_id,
            target_ref=payload.target_ref,
            target_type=payload.target_type,
            metadata=payload.metadata,
            actor=actor_for(request),
        )
        return target_out(row)
    except Exception as error:  # noqa: BLE001
        raise handle_error(error) from error


@app.get("/engagements/{engagement_id}/targets", response_model=list[TargetOut], tags=["targets"])
def list_targets(
    engagement_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    service: IntakeService = Depends(service_dep),
) -> list[TargetOut]:
    try:
        rows = service.list_targets(engagement_id)
        return [target_out(row) for row in rows[offset : offset + limit]]
    except Exception as error:  # noqa: BLE001
        raise handle_error(error) from error


@app.post(
    "/engagements/{engagement_id}/artifacts",
    response_model=ArtifactOut,
    status_code=status.HTTP_201_CREATED,
    tags=["artifacts"],
)
async def upload_artifact(
    engagement_id: str,
    request: Request,
    file: UploadFile = File(...),
    service: IntakeService = Depends(service_dep),
) -> ArtifactOut:
    try:
        data = await file.read(settings.maximum_upload_bytes + 1)
        if len(data) > settings.maximum_upload_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail="artifact exceeds configured upload limit",
            )
        media_type = file.content_type or "application/octet-stream"
        row = service.ingest_artifact_bytes(
            engagement_id=engagement_id,
            data=data,
            media_type=media_type,
            source="api-upload",
            metadata={"filename": file.filename},
            actor=actor_for(request),
        )
        return artifact_out(row)
    except HTTPException:
        raise
    except Exception as error:  # noqa: BLE001
        raise handle_error(error) from error


@app.get("/engagements/{engagement_id}/artifacts", response_model=list[ArtifactOut], tags=["artifacts"])
def list_artifacts(
    engagement_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    service: IntakeService = Depends(service_dep),
) -> list[ArtifactOut]:
    try:
        rows = service.list_artifacts(engagement_id)
        return [artifact_out(row) for row in rows[offset : offset + limit]]
    except Exception as error:  # noqa: BLE001
        raise handle_error(error) from error


@app.get("/tools", response_model=list[ToolSpecOut], tags=["tools"])
def list_tools(service: IntakeService = Depends(service_dep)) -> list[ToolSpecOut]:
    return [ToolSpecOut(**row) for row in service.list_tools()]


@app.get("/tools/status", response_model=list[ToolStatusOut], tags=["tools"])
def tools_status(service: IntakeService = Depends(service_dep)) -> list[ToolStatusOut]:
    return [ToolStatusOut(**row) for row in service.tool_status()]


@app.post("/authorize", response_model=ToolCallDecision, tags=["tools"])
async def authorize_tool_call(
    payload: ToolCallRequest,
    request: Request,
    service: IntakeService = Depends(service_dep),
) -> ToolCallDecision:
    try:
        effective = payload.model_copy(update={"actor": actor_for(request, payload.actor)})
        result = await service.propose_tool_call(effective)
        return result.decision
    except Exception as error:  # noqa: BLE001
        raise handle_error(error) from error


@app.post("/tool-calls", response_model=ToolCallProposeOut, status_code=status.HTTP_201_CREATED, tags=["tools"])
async def propose_tool_call(
    payload: ToolCallRequest,
    request: Request,
    service: IntakeService = Depends(service_dep),
) -> ToolCallProposeOut:
    try:
        effective = payload.model_copy(update={"actor": actor_for(request, payload.actor)})
        result = await service.propose_tool_call(effective)
        return ToolCallProposeOut(
            tool_call_id=result.tool_call_id,
            status=result.status,
            approval_id=result.approval_id,
            decision=result.decision,
        )
    except Exception as error:  # noqa: BLE001
        raise handle_error(error) from error


@app.post(
    "/tool-calls/{tool_call_id}/execute",
    response_model=ToolExecutionOut,
    tags=["tools"],
    deprecated=True,
)
async def execute_tool_call(
    tool_call_id: str,
    service: IntakeService = Depends(service_dep),
) -> ToolExecutionOut:
    try:
        result = await service.execute_tool_call(tool_call_id)
        return ToolExecutionOut(**result.model_dump(mode="json"))
    except Exception as error:  # noqa: BLE001
        raise handle_error(error) from error


@app.get("/engagements/{engagement_id}/tool-calls", response_model=list[ToolCallOut], tags=["tools"])
def list_tool_calls(
    engagement_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    service: IntakeService = Depends(service_dep),
) -> list[ToolCallOut]:
    try:
        rows = service.list_tool_calls(engagement_id)
        return [tool_call_out(row) for row in rows[offset : offset + limit]]
    except Exception as error:  # noqa: BLE001
        raise handle_error(error) from error


@app.get("/approvals/pending", response_model=list[ApprovalOut], tags=["approvals"])
def pending_approvals(service: IntakeService = Depends(service_dep)) -> list[ApprovalOut]:
    return [approval_out(row) for row in service.list_pending_approvals()]


@app.post("/approvals/{approval_id}/decision", response_model=ApprovalOut, tags=["approvals"])
def decide_approval(
    approval_id: str,
    payload: ApprovalDecision,
    request: Request,
    service: IntakeService = Depends(service_dep),
) -> ApprovalOut:
    try:
        row = service.decide_approval(
            approval_id,
            approved=payload.approved,
            decided_by=actor_for(request, payload.decided_by),
            reason=payload.reason,
        )
        return approval_out(row)
    except Exception as error:  # noqa: BLE001
        raise handle_error(error) from error


@app.post(
    "/engagements/{engagement_id}/evidence",
    response_model=EvidenceOut,
    status_code=status.HTTP_201_CREATED,
    tags=["evidence"],
)
def record_evidence(
    engagement_id: str,
    payload: EvidenceCreate,
    request: Request,
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
            actor=actor_for(request),
        )
        return evidence_out(row)
    except Exception as error:  # noqa: BLE001
        raise handle_error(error) from error


@app.get("/engagements/{engagement_id}/evidence", response_model=list[EvidenceOut], tags=["evidence"])
def list_evidence(
    engagement_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    service: IntakeService = Depends(service_dep),
) -> list[EvidenceOut]:
    try:
        rows = service.list_evidence(engagement_id)
        return [evidence_out(row) for row in rows[offset : offset + limit]]
    except Exception as error:  # noqa: BLE001
        raise handle_error(error) from error


@app.get("/evidence/{evidence_id}/download", tags=["evidence"])
def download_evidence(evidence_id: str, service: IntakeService = Depends(service_dep)) -> Response:
    try:
        evidence, data = service.get_evidence_bytes(evidence_id)
        return Response(
            content=data,
            media_type=evidence.media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{evidence.id}"',
                "X-Content-SHA256": evidence.sha256,
            },
        )
    except Exception as error:  # noqa: BLE001
        raise handle_error(error) from error


@app.post(
    "/engagements/{engagement_id}/findings",
    response_model=FindingOut,
    status_code=status.HTTP_201_CREATED,
    tags=["findings"],
)
def create_finding(
    engagement_id: str,
    payload: FindingCreate,
    request: Request,
    service: IntakeService = Depends(service_dep),
) -> FindingOut:
    try:
        row = service.create_finding(
            engagement_id=engagement_id,
            title=payload.title,
            description=payload.description,
            severity=payload.severity,
            evidence_ids=payload.evidence_ids,
            actor=actor_for(request),
        )
        return finding_out(row)
    except Exception as error:  # noqa: BLE001
        raise handle_error(error) from error


@app.get("/engagements/{engagement_id}/findings", response_model=list[FindingOut], tags=["findings"])
def list_findings(
    engagement_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    service: IntakeService = Depends(service_dep),
) -> list[FindingOut]:
    try:
        rows = service.list_findings(engagement_id)
        return [finding_out(row) for row in rows[offset : offset + limit]]
    except Exception as error:  # noqa: BLE001
        raise handle_error(error) from error


@app.get("/audit", response_model=list[AuditLogOut], tags=["audit"])
def list_audit(
    limit: int = Query(default=100, ge=1, le=1000),
    service: IntakeService = Depends(service_dep),
) -> list[AuditLogOut]:
    return [audit_log_out(row) for row in service.list_audit_logs(limit=limit)]


@app.get("/engagements/{engagement_id}/report.md", tags=["reports"])
def report_markdown(engagement_id: str, service: IntakeService = Depends(service_dep)) -> Response:
    try:
        engagement = service.get_engagement(engagement_id)
        findings = service.list_findings(engagement_id)
        body = render_markdown_report(engagement=engagement, findings=findings)
        return Response(content=body, media_type="text/markdown")
    except Exception as error:  # noqa: BLE001
        raise handle_error(error) from error
