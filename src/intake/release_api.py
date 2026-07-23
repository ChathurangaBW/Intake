from __future__ import annotations

from collections.abc import Generator

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from intake.auth import principal_from_request
from intake.config import settings
from intake.db import get_session
from intake.jobs import JobService
from intake.lifecycle import LifecycleService
from intake.models import Artifact
from intake.release_schemas import (
    EvidenceIntegrityOut,
    FindingUpdate,
    JobEnqueueRequest,
    JobOut,
    job_out,
)
from intake.runtime_schemas import ArtifactOut, FindingOut, artifact_out, finding_out
from intake.services import IntakeError, IntakeService, NotFoundError
from intake.storage import sha256_bytes

router = APIRouter()


def session_dep() -> Generator[Session, None, None]:
    yield from get_session()


def job_service_dep(session: Session = Depends(session_dep)) -> JobService:
    return JobService(session)


def lifecycle_service_dep(session: Session = Depends(session_dep)) -> LifecycleService:
    return LifecycleService(session)


def intake_service_dep(session: Session = Depends(session_dep)) -> IntakeService:
    return IntakeService(session)


def _http_error(error: Exception) -> HTTPException:
    if isinstance(error, NotFoundError):
        return HTTPException(status_code=404, detail=str(error))
    if isinstance(error, IntakeError):
        return HTTPException(status_code=400, detail=str(error))
    return HTTPException(status_code=500, detail="internal error")


def _find_artifact(service: IntakeService, engagement_id: str, digest: str) -> Artifact | None:
    stmt = (
        select(Artifact)
        .where(Artifact.engagement_id == engagement_id, Artifact.sha256 == digest)
        .limit(1)
    )
    return service.session.scalar(stmt)


@router.post(
    "/engagements/{engagement_id}/artifacts",
    response_model=ArtifactOut,
    status_code=status.HTTP_201_CREATED,
    tags=["artifacts"],
    include_in_schema=False,
)
async def upload_artifact_idempotent(
    engagement_id: str,
    request: Request,
    file: UploadFile = File(...),
    service: IntakeService = Depends(intake_service_dep),
) -> ArtifactOut:
    """Runtime override providing idempotent, race-safe artifact ingestion."""
    principal = principal_from_request(request)
    data = await file.read(settings.maximum_upload_bytes + 1)
    if len(data) > settings.maximum_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="artifact exceeds configured upload limit",
        )

    digest = sha256_bytes(data)
    existing = _find_artifact(service, engagement_id, digest)
    if existing is not None:
        service.audit(
            actor=principal.key_id,
            action="artifact.reuse",
            subject=existing.id,
            outcome="success",
            metadata={"engagement_id": engagement_id, "sha256": digest},
        )
        service.session.commit()
        return artifact_out(existing)

    try:
        row = service.ingest_artifact_bytes(
            engagement_id=engagement_id,
            data=data,
            media_type=file.content_type or "application/octet-stream",
            source="api-upload",
            metadata={"filename": file.filename},
            actor=principal.key_id,
        )
        return artifact_out(row)
    except IntegrityError:
        # A concurrent request may have inserted the same content after the
        # initial lookup. The unique constraint is the final authority.
        service.session.rollback()
        existing = _find_artifact(service, engagement_id, digest)
        if existing is None:
            raise
        service.audit(
            actor=principal.key_id,
            action="artifact.reuse",
            subject=existing.id,
            outcome="race_deduplicated",
            metadata={"engagement_id": engagement_id, "sha256": digest},
        )
        service.session.commit()
        return artifact_out(existing)


@router.post(
    "/tool-calls/{tool_call_id}/enqueue",
    response_model=JobOut,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["jobs"],
)
def enqueue_tool_call(
    tool_call_id: str,
    payload: JobEnqueueRequest,
    request: Request,
    jobs: JobService = Depends(job_service_dep),
) -> JobOut:
    principal = principal_from_request(request)
    try:
        return job_out(
            jobs.enqueue(
                tool_call_id,
                actor=principal.key_id,
                priority=payload.priority,
                max_attempts=payload.max_attempts,
            )
        )
    except Exception as error:  # noqa: BLE001
        raise _http_error(error) from error


@router.get("/jobs", response_model=list[JobOut], tags=["jobs"])
def list_jobs(
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    jobs: JobService = Depends(job_service_dep),
) -> list[JobOut]:
    return [job_out(row) for row in jobs.list(status=status_filter, limit=limit, offset=offset)]


@router.get("/jobs/{job_id}", response_model=JobOut, tags=["jobs"])
def get_job(job_id: str, jobs: JobService = Depends(job_service_dep)) -> JobOut:
    try:
        return job_out(jobs.get(job_id))
    except Exception as error:  # noqa: BLE001
        raise _http_error(error) from error


@router.post("/jobs/{job_id}/cancel", response_model=JobOut, tags=["jobs"])
def cancel_job(
    job_id: str,
    request: Request,
    jobs: JobService = Depends(job_service_dep),
) -> JobOut:
    principal = principal_from_request(request)
    try:
        return job_out(jobs.cancel(job_id, actor=principal.key_id))
    except Exception as error:  # noqa: BLE001
        raise _http_error(error) from error


@router.post(
    "/evidence/{evidence_id}/verify",
    response_model=EvidenceIntegrityOut,
    tags=["evidence"],
)
def verify_evidence(
    evidence_id: str,
    request: Request,
    lifecycle: LifecycleService = Depends(lifecycle_service_dep),
) -> EvidenceIntegrityOut:
    principal = principal_from_request(request)
    try:
        evidence, result = lifecycle.verify_evidence(evidence_id, actor=principal.key_id)
        return EvidenceIntegrityOut(
            evidence_id=evidence.id,
            expected_sha256=result.expected_sha256,
            actual_sha256=result.actual_sha256,
            expected_size_bytes=evidence.size_bytes,
            actual_size_bytes=result.actual_size_bytes,
            digest_matches=result.digest_matches,
            size_matches=result.size_matches,
            valid=result.valid,
        )
    except Exception as error:  # noqa: BLE001
        raise _http_error(error) from error


@router.patch("/findings/{finding_id}", response_model=FindingOut, tags=["findings"])
def update_finding(
    finding_id: str,
    payload: FindingUpdate,
    request: Request,
    lifecycle: LifecycleService = Depends(lifecycle_service_dep),
) -> FindingOut:
    principal = principal_from_request(request)
    try:
        return finding_out(lifecycle.update_finding(finding_id, payload, actor=principal.key_id))
    except Exception as error:  # noqa: BLE001
        raise _http_error(error) from error
