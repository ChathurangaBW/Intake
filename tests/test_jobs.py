from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest

from intake.jobs import JobService
from intake.models import ExecutionJob, ToolCall

pytestmark = pytest.mark.unit


class FakeSession:
    def __init__(self) -> None:
        self.objects: dict[tuple[type[Any], str], Any] = {}
        self.added: list[Any] = []
        self.scalar_result: Any = None

    def get(self, model: type[Any], key: str) -> Any:
        return self.objects.get((model, key))

    def scalar(self, _statement: Any) -> Any:
        return self.scalar_result

    def add(self, row: Any) -> None:
        if getattr(row, "id", None) is None:
            row.id = str(uuid4())
        self.objects[(type(row), row.id)] = row
        self.added.append(row)

    def flush(self) -> None:
        return None

    def commit(self) -> None:
        return None

    def rollback(self) -> None:
        return None

    def refresh(self, _row: Any) -> None:
        return None


def tool_call(status: str = "authorized") -> ToolCall:
    return ToolCall(
        id="tool-1",
        engagement_id="eng-1",
        actor="qa",
        tool="ghidra",
        operation="analyze",
        risk="read_only",
        request_json={},
        status=status,
    )


def test_enqueue_authorized_tool_call() -> None:
    session = FakeSession()
    tool = tool_call()
    session.objects[(ToolCall, tool.id)] = tool

    job = JobService(session).enqueue(tool.id, actor="qa", priority=5, max_attempts=2)

    assert job.status == "queued"
    assert job.priority == 5
    assert job.max_attempts == 2
    assert tool.status == "queued"


def test_cancel_queued_job_updates_tool_call() -> None:
    session = FakeSession()
    tool = tool_call(status="queued")
    job = ExecutionJob(id="job-1", tool_call_id=tool.id, status="queued")
    session.objects[(ToolCall, tool.id)] = tool
    session.objects[(ExecutionJob, job.id)] = job

    result = JobService(session).cancel(job.id, actor="qa")

    assert result.status == "cancelled"
    assert result.cancel_requested
    assert tool.status == "cancelled"


def test_completion_honors_running_cancellation_request() -> None:
    session = FakeSession()
    tool = tool_call(status="running")
    job = ExecutionJob(
        id="job-1",
        tool_call_id=tool.id,
        status="running",
        leased_by="worker-1",
        cancel_requested=True,
    )
    session.objects[(ToolCall, tool.id)] = tool
    session.objects[(ExecutionJob, job.id)] = job

    result = JobService(session).complete(
        job.id,
        worker_id="worker-1",
        result={"status": "completed"},
    )

    assert result.status == "cancelled"
    assert result.result_json == {}
    assert tool.status == "cancelled"
