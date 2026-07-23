from __future__ import annotations

from collections.abc import Generator

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from intake.db import get_session
from intake.ops import audit_ndjson, engagement_export_bundle, readiness_report, verify_evidence_inventory
from intake.services import IntakeError, NotFoundError, ScopeError

router = APIRouter(prefix="/ops", tags=["operations"])


def session_dep() -> Generator[Session, None, None]:
    yield from get_session()


def _raise_http(error: Exception) -> None:
    from fastapi import HTTPException, status

    if isinstance(error, NotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    if isinstance(error, ScopeError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error)) from error
    if isinstance(error, IntakeError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="internal error") from error


@router.get("/readiness")
def readiness(session: Session = Depends(session_dep)) -> dict:
    """Return operator-facing readiness diagnostics."""
    return readiness_report(session)


@router.get("/engagements/{engagement_id}/export")
def export_engagement(engagement_id: str, session: Session = Depends(session_dep)) -> dict:
    """Export an engagement metadata bundle without raw evidence bytes."""
    try:
        return engagement_export_bundle(session, engagement_id)
    except Exception as error:  # noqa: BLE001
        _raise_http(error)
        raise


@router.get("/audit/export.ndjson")
def export_audit_ndjson(
    limit: int = Query(default=1000, ge=1, le=10000),
    session: Session = Depends(session_dep),
) -> Response:
    """Export recent audit events as canonical newline-delimited JSON."""
    body = audit_ndjson(session, limit=limit)
    return Response(
        content=body,
        media_type="application/x-ndjson",
        headers={"Content-Disposition": 'attachment; filename="intake-audit.ndjson"'},
    )


@router.get("/evidence/verify")
def verify_evidence(
    limit: int = Query(default=500, ge=1, le=5000),
    session: Session = Depends(session_dep),
) -> dict:
    """Verify stored evidence digest and size for recent evidence records."""
    return verify_evidence_inventory(session, limit=limit)
