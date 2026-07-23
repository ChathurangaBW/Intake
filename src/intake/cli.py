from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import typer
import yaml

from intake.db import SessionLocal
from intake.evidence import make_evidence_record
from intake.reporting import render_markdown_report
from intake.runtime_schemas import (
    artifact_out,
    audit_log_out,
    engagement_out,
    evidence_out,
    finding_out,
    target_out,
    tool_call_out,
)
from intake.schemas import RiskLevel, ToolCallRequest
from intake.services import IntakeService

app = typer.Typer(help="Intake security automation framework")
engagement_app = typer.Typer(help="Create and inspect engagements")
target_app = typer.Typer(help="Manage scoped targets")
artifact_app = typer.Typer(help="Ingest and list artifacts")
tool_app = typer.Typer(help="Propose, approve, and execute policy-gated tool calls")
evidence_app = typer.Typer(help="Inspect and export evidence")
finding_app = typer.Typer(help="Record and report findings")
audit_app = typer.Typer(help="Inspect audit events")

app.add_typer(engagement_app, name="engagement")
app.add_typer(target_app, name="target")
app.add_typer(artifact_app, name="artifact")
app.add_typer(tool_app, name="tool")
app.add_typer(evidence_app, name="evidence")
app.add_typer(finding_app, name="finding")
app.add_typer(audit_app, name="audit")


def _echo_json(value: Any) -> None:
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    typer.echo(json.dumps(value, indent=2, sort_keys=True, default=str))


def _load_manifest(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise typer.BadParameter("manifest must be a YAML mapping")
    return data


@app.command()
def doctor() -> None:
    """Check that the CLI is installed."""
    typer.echo("Intake CLI is installed.")


@app.command()
def serve(host: str = "127.0.0.1", port: int = 8000, reload: bool = False) -> None:
    """Run the FastAPI service."""
    import uvicorn

    uvicorn.run("intake.api:app", host=host, port=port, reload=reload)


@app.command()
def stats() -> None:
    """Print dashboard statistics."""
    with SessionLocal() as session:
        service = IntakeService(session)
        _echo_json(service.dashboard_stats())


@app.command()
def hash_artifact(path: Path, media_type: str = "application/octet-stream") -> None:
    """Create a local evidence record for a file without storing it remotely."""
    if not path.exists() or not path.is_file():
        raise typer.BadParameter(f"Not a file: {path}")
    record = make_evidence_record(path, media_type=media_type, source_tool="intake.hash_artifact")
    typer.echo(record.model_dump_json(indent=2))


@engagement_app.command("create")
def create_engagement(
    engagement_id: str,
    name: str,
    classification: str = "internal",
    manifest: Path | None = None,
) -> None:
    """Create an active engagement with an optional YAML manifest."""
    with SessionLocal() as session:
        service = IntakeService(session)
        row = service.create_engagement(
            engagement_id=engagement_id,
            name=name,
            classification=classification,
            manifest=_load_manifest(manifest),
        )
        _echo_json(engagement_out(row))


@engagement_app.command("list")
def list_engagements() -> None:
    """List engagements."""
    with SessionLocal() as session:
        service = IntakeService(session)
        _echo_json([engagement_out(row).model_dump(mode="json") for row in service.list_engagements()])


@target_app.command("add")
def add_target(engagement_id: str, target_ref: str, target_type: str = "domain") -> None:
    """Add an explicitly authorized target to an engagement."""
    with SessionLocal() as session:
        service = IntakeService(session)
        row = service.add_target(engagement_id=engagement_id, target_ref=target_ref, target_type=target_type)
        _echo_json(target_out(row))


@target_app.command("list")
def list_targets(engagement_id: str) -> None:
    """List authorized targets for an engagement."""
    with SessionLocal() as session:
        service = IntakeService(session)
        _echo_json([target_out(row).model_dump(mode="json") for row in service.list_targets(engagement_id)])


@artifact_app.command("ingest")
def ingest_artifact(
    engagement_id: str,
    path: Path,
    media_type: str = "application/octet-stream",
    source: str = "manual",
) -> None:
    """Store an artifact in content-addressed evidence storage and the DB."""
    if not path.exists() or not path.is_file():
        raise typer.BadParameter(f"Not a file: {path}")
    with SessionLocal() as session:
        service = IntakeService(session)
        row = service.ingest_artifact(engagement_id=engagement_id, path=path, media_type=media_type, source=source)
        _echo_json(artifact_out(row))


@artifact_app.command("list")
def list_artifacts(engagement_id: str) -> None:
    """List stored artifacts for an engagement."""
    with SessionLocal() as session:
        service = IntakeService(session)
        _echo_json([artifact_out(row).model_dump(mode="json") for row in service.list_artifacts(engagement_id)])


@tool_app.command("catalog")
def tool_catalog() -> None:
    """List supported typed tools."""
    with SessionLocal() as session:
        service = IntakeService(session)
        _echo_json(service.list_tools())


@tool_app.command("status")
def tool_status() -> None:
    """Show worker/tool availability."""
    with SessionLocal() as session:
        service = IntakeService(session)
        _echo_json(service.tool_status())


@tool_app.command("propose")
def propose_tool_call(
    engagement_id: str,
    actor: str,
    tool: str,
    operation: str,
    risk: RiskLevel = RiskLevel.READ_ONLY,
    arguments_json: str = "{}",
) -> None:
    """Propose a typed tool call and persist the policy decision."""
    try:
        arguments = json.loads(arguments_json)
    except json.JSONDecodeError as error:
        raise typer.BadParameter(f"invalid JSON: {error}") from error
    if not isinstance(arguments, dict):
        raise typer.BadParameter("arguments_json must decode to an object")

    request = ToolCallRequest(
        engagement_id=engagement_id,
        actor=actor,
        tool=tool,
        operation=operation,
        risk=risk,
        arguments=arguments,
    )

    async def _run() -> None:
        with SessionLocal() as session:
            service = IntakeService(session)
            result = await service.propose_tool_call(request)
            _echo_json(
                {
                    "tool_call_id": result.tool_call_id,
                    "status": result.status,
                    "approval_id": result.approval_id,
                    "decision": result.decision.model_dump(mode="json"),
                }
            )

    asyncio.run(_run())


@tool_app.command("execute")
def execute_tool_call(tool_call_id: str) -> None:
    """Execute an already-authorized tool call through the constrained runtime."""

    async def _run() -> None:
        with SessionLocal() as session:
            service = IntakeService(session)
            result = await service.execute_tool_call(tool_call_id)
            _echo_json(result)

    asyncio.run(_run())


@tool_app.command("list")
def list_tool_calls(engagement_id: str) -> None:
    """List tool calls for an engagement."""
    with SessionLocal() as session:
        service = IntakeService(session)
        _echo_json([tool_call_out(row).model_dump(mode="json") for row in service.list_tool_calls(engagement_id)])


@tool_app.command("pending")
def pending_approvals() -> None:
    """List pending approvals."""
    with SessionLocal() as session:
        service = IntakeService(session)
        _echo_json(
            [
                {
                    "id": row.id,
                    "tool_call_id": row.tool_call_id,
                    "status": row.status,
                    "requested_by": row.requested_by,
                    "reason": row.reason,
                }
                for row in service.list_pending_approvals()
            ]
        )


@tool_app.command("approve")
def approve_tool_call(approval_id: str, decided_by: str, reason: str | None = None) -> None:
    """Approve a pending gated tool call."""
    with SessionLocal() as session:
        service = IntakeService(session)
        row = service.decide_approval(approval_id, approved=True, decided_by=decided_by, reason=reason)
        _echo_json({"id": row.id, "status": row.status, "tool_call_id": row.tool_call_id})


@tool_app.command("reject")
def reject_tool_call(approval_id: str, decided_by: str, reason: str | None = None) -> None:
    """Reject a pending gated tool call."""
    with SessionLocal() as session:
        service = IntakeService(session)
        row = service.decide_approval(approval_id, approved=False, decided_by=decided_by, reason=reason)
        _echo_json({"id": row.id, "status": row.status, "tool_call_id": row.tool_call_id})


@evidence_app.command("list")
def list_evidence(engagement_id: str) -> None:
    """List evidence records for an engagement."""
    with SessionLocal() as session:
        service = IntakeService(session)
        _echo_json([evidence_out(row).model_dump(mode="json") for row in service.list_evidence(engagement_id)])


@evidence_app.command("download")
def download_evidence(evidence_id: str, output: Path) -> None:
    """Download evidence bytes from content-addressed object storage."""
    with SessionLocal() as session:
        service = IntakeService(session)
        _, data = service.get_evidence_bytes(evidence_id)
        output.write_bytes(data)
        typer.echo(str(output))


@finding_app.command("create")
def create_finding(
    engagement_id: str,
    title: str,
    description: str,
    severity: str = "informational",
    evidence_ids_json: str = "[]",
) -> None:
    """Create a draft finding."""
    try:
        evidence_ids = json.loads(evidence_ids_json)
    except json.JSONDecodeError as error:
        raise typer.BadParameter(f"invalid evidence JSON: {error}") from error
    if not isinstance(evidence_ids, list):
        raise typer.BadParameter("evidence_ids_json must decode to a list")

    with SessionLocal() as session:
        service = IntakeService(session)
        row = service.create_finding(
            engagement_id=engagement_id,
            title=title,
            description=description,
            severity=severity,
            evidence_ids=evidence_ids,
        )
        _echo_json(finding_out(row))


@finding_app.command("list")
def list_findings(engagement_id: str) -> None:
    """List findings."""
    with SessionLocal() as session:
        service = IntakeService(session)
        _echo_json([finding_out(row).model_dump(mode="json") for row in service.list_findings(engagement_id)])


@finding_app.command("report")
def report(engagement_id: str, output: Path | None = None) -> None:
    """Render a markdown assessment report."""
    with SessionLocal() as session:
        service = IntakeService(session)
        engagement = service.get_engagement(engagement_id)
        findings = service.list_findings(engagement_id)
        body = render_markdown_report(engagement=engagement, findings=findings)
    if output is not None:
        output.write_text(body, encoding="utf-8")
        typer.echo(str(output))
    else:
        typer.echo(body)


@audit_app.command("list")
def list_audit(limit: int = 100) -> None:
    """List recent audit events."""
    with SessionLocal() as session:
        service = IntakeService(session)
        _echo_json([audit_log_out(row).model_dump(mode="json") for row in service.list_audit_logs(limit=limit)])
