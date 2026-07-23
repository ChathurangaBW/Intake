from __future__ import annotations

from collections.abc import Generator

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from intake.auth import principal_from_request
from intake.db import get_session
from intake.jobs import JobService
from intake.lifecycle import LifecycleService
from intake.release_schemas import (
    EvidenceIntegrityOut,
    FindingUpdate,
    JobEnqueueRequest,
    JobOut,
    job_out,
)
from intake.runtime_schemas import FindingOut, finding_out
from intake.services import IntakeError, NotFoundError

router = APIRouter()


def session_dep() -> Generator[Session, None, None]:
    yield from get_session()


def job_service_dep(session: Session = Depends(session_dep)) -> JobService:
    return JobService(session)


def lifecycle_service_dep(session: Session = Depends(session_dep)) -> LifecycleService:
    return LifecycleService(session)


def _http_error(error: Exception) -> HTTPException:
    if isinstance(error, NotFoundError):
        return HTTPException(status_code=404, detail=str(error))
    if isinstance(error, IntakeError):
        return HTTPException(status_code=400, detail=str(error))
    return HTTPException(status_code=500, detail="internal error")


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
