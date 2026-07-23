from __future__ import annotations

import json
import subprocess
from pathlib import Path

import typer

from intake.cli import _echo_json, app, evidence_app, finding_app
from intake.db import SessionLocal
from intake.jobs import JobService
from intake.lifecycle import LifecycleService
from intake.release_schemas import FindingUpdate, job_out
from intake.runtime_schemas import finding_out

job_app = typer.Typer(help="Manage durable execution jobs")
app.add_typer(job_app, name="job")


@app.command("init")
def init_env(
    output: Path = typer.Option(Path(".env"), "--output", "-o"),
    force: bool = typer.Option(False, "--force"),
) -> None:
    """Create a local environment file from the production-safe example."""
    if output.exists() and not force:
        raise typer.BadParameter(f"{output} already exists; use --force to overwrite")
    source = Path("examples/env/production.env.example")
    if not source.exists():
        source = Path(".env.example")
    output.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    typer.echo(f"wrote {output}")


@app.command("demo")
def seed_demo() -> None:
    """Seed a harmless local demo engagement."""
    subprocess.run(["python", "scripts/seed_demo.py"], check=True)


@app.command("release-info")
def release_info() -> None:
    """Print the release manifest."""
    manifest = Path("release/manifest-1.0.0.json")
    if not manifest.exists():
        raise typer.BadParameter("release manifest not found")
    typer.echo(json.dumps(json.loads(manifest.read_text(encoding="utf-8")), indent=2))


@app.command("doctor-full")
def doctor_full() -> None:
    """Check local operator prerequisites."""
    checks = {
        "docker-compose": ["docker", "compose", "version"],
        "python": ["python", "--version"],
    }
    result: dict[str, str] = {}
    for name, command in checks.items():
        try:
            completed = subprocess.run(command, check=True, capture_output=True, text=True)
            result[name] = (completed.stdout or completed.stderr).strip()
        except Exception as error:  # noqa: BLE001 - diagnostic command
            result[name] = f"missing or failed: {error}"
    typer.echo(json.dumps(result, indent=2))


@job_app.command("enqueue")
def enqueue_job(
    tool_call_id: str,
    actor: str = "operator",
    priority: int = typer.Option(100, min=0, max=1000),
    max_attempts: int = typer.Option(3, min=1, max=10),
) -> None:
    """Queue an authorized tool call for the durable worker."""
    with SessionLocal() as session:
        row = JobService(session).enqueue(
            tool_call_id,
            actor=actor,
            priority=priority,
            max_attempts=max_attempts,
        )
        _echo_json(job_out(row))


@job_app.command("list")
def list_jobs(
    status_filter: str | None = typer.Option(None, "--status"),
    limit: int = typer.Option(100, min=1, max=500),
    offset: int = typer.Option(0, min=0),
) -> None:
    """List durable execution jobs."""
    with SessionLocal() as session:
        rows = JobService(session).list(status=status_filter, limit=limit, offset=offset)
        _echo_json([job_out(row).model_dump(mode="json") for row in rows])


@job_app.command("get")
def get_job(job_id: str) -> None:
    """Inspect one durable execution job."""
    with SessionLocal() as session:
        _echo_json(job_out(JobService(session).get(job_id)))


@job_app.command("cancel")
def cancel_job(job_id: str, actor: str = "operator") -> None:
    """Request cancellation of a queued or running job."""
    with SessionLocal() as session:
        _echo_json(job_out(JobService(session).cancel(job_id, actor=actor)))


@evidence_app.command("verify")
def verify_evidence(evidence_id: str, actor: str = "operator") -> None:
    """Re-read stored evidence and verify its digest and size."""
    with SessionLocal() as session:
        evidence, result = LifecycleService(session).verify_evidence(evidence_id, actor=actor)
        _echo_json(
            {
                "evidence_id": evidence.id,
                "expected_sha256": result.expected_sha256,
                "actual_sha256": result.actual_sha256,
                "expected_size_bytes": evidence.size_bytes,
                "actual_size_bytes": result.actual_size_bytes,
                "digest_matches": result.digest_matches,
                "size_matches": result.size_matches,
                "valid": result.valid,
            }
        )


@finding_app.command("update")
def update_finding(
    finding_id: str,
    actor: str = "operator",
    severity: str | None = None,
    status: str | None = None,
    verification_status: str | None = None,
    title: str | None = None,
    description: str | None = None,
) -> None:
    """Update finding review and verification lifecycle fields."""
    payload = FindingUpdate(
        severity=severity,
        status=status,
        verification_status=verification_status,
        title=title,
        description=description,
    )
    with SessionLocal() as session:
        row = LifecycleService(session).update_finding(finding_id, payload, actor=actor)
        _echo_json(finding_out(row))
