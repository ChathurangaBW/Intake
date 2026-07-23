from __future__ import annotations

from datetime import timedelta

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from intake.config import settings
from intake.models import AuditLog, ExecutionJob, ToolCall, utcnow
from intake.services import IntakeError, NotFoundError

TERMINAL_JOB_STATUSES = {"completed", "failed", "cancelled"}


class JobService:
    """Durable database-backed execution queue."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def _audit(
        self,
        *,
        actor: str,
        action: str,
        subject: str,
        outcome: str,
        metadata: dict[str, object] | None = None,
    ) -> None:
        self.session.add(
            AuditLog(
                actor=actor,
                action=action,
                subject=subject,
                outcome=outcome,
                metadata_=metadata or {},
            )
        )

    def get(self, job_id: str) -> ExecutionJob:
        job = self.session.get(ExecutionJob, job_id)
        if job is None:
            raise NotFoundError(f"unknown execution job: {job_id}")
        return job

    def list(
        self,
        *,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ExecutionJob]:
        safe_limit = min(max(limit, 1), 500)
        safe_offset = max(offset, 0)
        stmt = (
            select(ExecutionJob)
            .order_by(ExecutionJob.created_at.desc())
            .limit(safe_limit)
            .offset(safe_offset)
        )
        if status is not None:
            stmt = stmt.where(ExecutionJob.status == status)
        return list(self.session.scalars(stmt))

    def enqueue(
        self,
        tool_call_id: str,
        *,
        actor: str,
        priority: int = 100,
        max_attempts: int = 3,
    ) -> ExecutionJob:
        tool_call = self.session.get(ToolCall, tool_call_id)
        if tool_call is None:
            raise NotFoundError(f"unknown tool call: {tool_call_id}")
        if tool_call.status != "authorized":
            raise IntakeError(f"tool call is not authorized: {tool_call.status}")

        existing = self.session.scalar(
            select(ExecutionJob).where(ExecutionJob.tool_call_id == tool_call_id)
        )
        if existing is not None:
            return existing

        job = ExecutionJob(
            tool_call_id=tool_call_id,
            status="queued",
            priority=min(max(priority, 0), 1000),
            max_attempts=min(max(max_attempts, 1), 10),
        )
        tool_call.status = "queued"
        self.session.add(job)
        self.session.flush()
        self._audit(
            actor=actor,
            action="job.enqueue",
            subject=job.id,
            outcome="queued",
            metadata={"tool_call_id": tool_call_id, "priority": job.priority},
        )
        self.session.commit()
        self.session.refresh(job)
        return job

    def claim_next(self, worker_id: str) -> ExecutionJob | None:
        now = utcnow()
        reclaimable = or_(
            ExecutionJob.status == "queued",
            (ExecutionJob.status == "running") & (ExecutionJob.leased_until < now),
        )
        stmt = (
            select(ExecutionJob)
            .where(reclaimable)
            .where(ExecutionJob.cancel_requested.is_(False))
            .where(ExecutionJob.attempts < ExecutionJob.max_attempts)
            .order_by(ExecutionJob.priority.asc(), ExecutionJob.created_at.asc())
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        job = self.session.scalar(stmt)
        if job is None:
            self.session.rollback()
            return None

        job.status = "running"
        job.leased_by = worker_id
        job.leased_until = now + timedelta(seconds=settings.job_lease_seconds)
        job.started_at = job.started_at or now
        job.attempts += 1
        job.error = None

        tool_call = self.session.get(ToolCall, job.tool_call_id)
        if tool_call is None:
            job.status = "failed"
            job.error = "tool call was deleted"
            job.finished_at = now
        else:
            tool_call.status = "running"
            tool_call.worker_id = worker_id

        self._audit(
            actor=worker_id,
            action="job.claim",
            subject=job.id,
            outcome=job.status,
            metadata={"tool_call_id": job.tool_call_id, "attempt": job.attempts},
        )
        self.session.commit()
        self.session.refresh(job)
        return job

    def heartbeat(self, job_id: str, worker_id: str) -> ExecutionJob:
        job = self.get(job_id)
        if job.status != "running" or job.leased_by != worker_id:
            raise IntakeError("job is not leased by this worker")
        job.leased_until = utcnow() + timedelta(seconds=settings.job_lease_seconds)
        self.session.commit()
        self.session.refresh(job)
        return job

    def complete(
        self,
        job_id: str,
        *,
        worker_id: str,
        result: dict[str, object],
    ) -> ExecutionJob:
        job = self.get(job_id)
        if job.leased_by != worker_id:
            raise IntakeError("job is not leased by this worker")

        cancelled = job.cancel_requested
        job.status = "cancelled" if cancelled else "completed"
        job.result_json = {} if cancelled else result
        job.error = "cancelled while running" if cancelled else None
        job.finished_at = utcnow()
        job.leased_by = None
        job.leased_until = None

        tool_call = self.session.get(ToolCall, job.tool_call_id)
        if tool_call is not None:
            tool_call.status = job.status
            tool_call.worker_id = None

        self._audit(
            actor=worker_id,
            action="job.complete",
            subject=job.id,
            outcome=job.status,
            metadata={"tool_call_id": job.tool_call_id},
        )
        self.session.commit()
        self.session.refresh(job)
        return job

    def fail(self, job_id: str, *, worker_id: str, error: str) -> ExecutionJob:
        job = self.get(job_id)
        if job.leased_by != worker_id:
            raise IntakeError("job is not leased by this worker")

        retryable = job.attempts < job.max_attempts and not job.cancel_requested
        job.status = "queued" if retryable else "failed"
        job.error = error[:4000]
        job.leased_by = None
        job.leased_until = None
        if not retryable:
            job.finished_at = utcnow()

        tool_call = self.session.get(ToolCall, job.tool_call_id)
        if tool_call is not None:
            tool_call.status = "queued" if retryable else "failed"
            tool_call.worker_id = None

        self._audit(
            actor=worker_id,
            action="job.fail",
            subject=job.id,
            outcome=job.status,
            metadata={
                "tool_call_id": job.tool_call_id,
                "attempt": job.attempts,
                "error": job.error,
            },
        )
        self.session.commit()
        self.session.refresh(job)
        return job

    def cancel(self, job_id: str, *, actor: str) -> ExecutionJob:
        job = self.get(job_id)
        if job.status in TERMINAL_JOB_STATUSES:
            return job
        job.cancel_requested = True
        if job.status == "queued":
            job.status = "cancelled"
            job.finished_at = utcnow()
            tool_call = self.session.get(ToolCall, job.tool_call_id)
            if tool_call is not None:
                tool_call.status = "cancelled"
        self._audit(
            actor=actor,
            action="job.cancel",
            subject=job.id,
            outcome=job.status,
            metadata={"tool_call_id": job.tool_call_id},
        )
        self.session.commit()
        self.session.refresh(job)
        return job
