from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class JobEnqueueRequest(BaseModel):
    priority: int = Field(default=100, ge=0, le=1000)
    max_attempts: int = Field(default=3, ge=1, le=10)


class JobOut(BaseModel):
    id: str
    tool_call_id: str
    status: str
    priority: int
    attempts: int
    max_attempts: int
    leased_by: str | None = None
    leased_until: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    cancel_requested: bool
    result: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    created_at: datetime
    updated_at: datetime


class EvidenceIntegrityOut(BaseModel):
    evidence_id: str
    expected_sha256: str
    actual_sha256: str
    expected_size_bytes: int
    actual_size_bytes: int
    digest_matches: bool
    size_matches: bool
    valid: bool


class FindingUpdate(BaseModel):
    severity: Literal["informational", "low", "medium", "high", "critical"] | None = None
    status: Literal["draft", "open", "accepted", "remediated", "closed"] | None = None
    verification_status: Literal["unverified", "verified", "rejected"] | None = None
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1)


def job_out(row: Any) -> JobOut:
    return JobOut(
        id=row.id,
        tool_call_id=row.tool_call_id,
        status=row.status,
        priority=row.priority,
        attempts=row.attempts,
        max_attempts=row.max_attempts,
        leased_by=row.leased_by,
        leased_until=row.leased_until,
        started_at=row.started_at,
        finished_at=row.finished_at,
        cancel_requested=row.cancel_requested,
        result=row.result_json,
        error=row.error,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
