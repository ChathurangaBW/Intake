from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient

from intake.api import app
from intake.release_api import job_service_dep, lifecycle_service_dep

pytestmark = pytest.mark.contract


def job_row(**overrides: Any) -> SimpleNamespace:
    now = datetime.now(UTC)
    values = {
        "id": "job-1",
        "tool_call_id": "tool-1",
        "status": "queued",
        "priority": 100,
        "attempts": 0,
        "max_attempts": 3,
        "leased_by": None,
        "leased_until": None,
        "started_at": None,
        "finished_at": None,
        "cancel_requested": False,
        "result_json": {},
        "error": None,
        "created_at": now,
        "updated_at": now,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class FakeJobs:
    def enqueue(self, *_args: Any, **_kwargs: Any) -> SimpleNamespace:
        return job_row()

    def list(self, **_kwargs: Any) -> list[SimpleNamespace]:
        return [job_row()]

    def get(self, _job_id: str) -> SimpleNamespace:
        return job_row()

    def cancel(self, _job_id: str, **_kwargs: Any) -> SimpleNamespace:
        return job_row(status="cancelled", cancel_requested=True, finished_at=datetime.now(UTC))


class FakeLifecycle:
    def verify_evidence(self, evidence_id: str, **_kwargs: Any) -> tuple[SimpleNamespace, SimpleNamespace]:
        evidence = SimpleNamespace(id=evidence_id, size_bytes=4)
        result = SimpleNamespace(
            expected_sha256="a" * 64,
            actual_sha256="a" * 64,
            actual_size_bytes=4,
            digest_matches=True,
            size_matches=True,
            valid=True,
        )
        return evidence, result

    def update_finding(self, finding_id: str, *_args: Any, **_kwargs: Any) -> SimpleNamespace:
        return SimpleNamespace(
            id=finding_id,
            engagement_id="eng-1",
            title="Updated",
            severity="high",
            status="open",
            verification_status="verified",
            description="Evidence-backed",
        )


@pytest.fixture(autouse=True)
def override_dependencies() -> None:
    app.dependency_overrides[job_service_dep] = lambda: FakeJobs()
    app.dependency_overrides[lifecycle_service_dep] = lambda: FakeLifecycle()
    yield
    app.dependency_overrides.clear()


def test_job_api_contract() -> None:
    client = TestClient(app)

    queued = client.post("/tool-calls/tool-1/enqueue", json={"priority": 10, "max_attempts": 2})
    assert queued.status_code == 202
    assert queued.json()["status"] == "queued"
    assert client.get("/jobs").status_code == 200
    assert client.get("/jobs/job-1").json()["id"] == "job-1"
    assert client.post("/jobs/job-1/cancel").json()["status"] == "cancelled"


def test_integrity_and_finding_lifecycle_contract() -> None:
    client = TestClient(app)

    verified = client.post("/evidence/evidence-1/verify")
    assert verified.status_code == 200
    assert verified.json()["valid"] is True

    finding = client.patch(
        "/findings/finding-1",
        json={"severity": "high", "status": "open", "verification_status": "verified"},
    )
    assert finding.status_code == 200
    assert finding.json()["verification_status"] == "verified"
