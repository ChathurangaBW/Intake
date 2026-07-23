from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient

from intake.api import app, service_dep
from intake.release_api import intake_service_dep
from intake.schemas import PolicyDecision, ToolCallDecision


@dataclass
class Row:
    id: str = "row-1"
    engagement_id: str = "eng-qa"
    name: str = "QA Engagement"
    status: str = "active"
    classification: str = "internal"
    manifest: dict[str, Any] = field(default_factory=dict)
    target_ref: str = "app.authorized.test"
    target_type: str = "domain"
    metadata_: dict[str, Any] = field(default_factory=dict)
    sha256: str = "a" * 64
    media_type: str = "text/plain"
    size_bytes: int = 4
    storage_uri: str = "s3://bucket/key"
    source: str = "test"
    actor: str = "qa"
    tool: str = "ghidra"
    operation: str = "analyze"
    tool_call_id: str = "tool-1"
    risk: str = "read_only"
    request_json: dict[str, Any] = field(default_factory=dict)
    requested_by: str = "qa"
    decided_by: str | None = None
    reason: str | None = None
    summary: str | None = "summary"
    title: str = "Finding"
    severity: str = "informational"
    verification_status: str = "unverified"
    description: str = "description"
    action: str = "test.action"
    subject: str = "row-1"
    outcome: str = "ok"
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


class FakeService:
    def __init__(self) -> None:
        self.session = self

    def scalar(self, _statement: Any) -> Any:
        return None

    def commit(self) -> None:
        return None

    def rollback(self) -> None:
        return None

    def audit(self, **_: Any) -> None:
        return None

    def dashboard_stats(self) -> dict[str, int]:
        return {
            "engagements": 1,
            "targets": 1,
            "artifacts": 1,
            "tool_calls": 1,
            "approvals_pending": 0,
            "evidence": 1,
            "findings": 1,
        }

    def create_engagement(self, **_: Any) -> Row:
        return Row(id="eng-qa")

    def list_engagements(self) -> list[Row]:
        return [Row(id="eng-qa")]

    def get_engagement(self, engagement_id: str) -> Row:
        return Row(id=engagement_id)

    def add_target(self, **_: Any) -> Row:
        return Row(id="target-1")

    def list_targets(self, engagement_id: str) -> list[Row]:
        return [Row(id="target-1", engagement_id=engagement_id)]

    def ingest_artifact_bytes(self, **_: Any) -> Row:
        return Row(id="artifact-1")

    def list_artifacts(self, engagement_id: str) -> list[Row]:
        return [Row(id="artifact-1", engagement_id=engagement_id)]

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "ghidra",
                "operation": "analyze",
                "risk": "read_only",
                "description": "Read-only analysis",
                "requires_artifact": True,
                "requires_target": False,
                "network_required": False,
            }
        ]

    def tool_status(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "ghidra",
                "operation": "analyze",
                "available": True,
                "runtime": "fake",
                "detail": "ok",
            }
        ]

    async def propose_tool_call(self, request: Any) -> Any:
        class Result:
            tool_call_id = "tool-1"
            status = "authorized"
            approval_id = None
            decision = ToolCallDecision(decision=PolicyDecision.ALLOW, reason="ok")

        return Result()

    async def execute_tool_call(self, tool_call_id: str) -> Any:
        class Result:
            def model_dump(self, mode: str = "json") -> dict[str, Any]:
                return {
                    "status": "completed",
                    "summary": tool_call_id,
                    "evidence_ids": [],
                    "data": {},
                }

        return Result()

    def list_tool_calls(self, engagement_id: str) -> list[Row]:
        return [Row(id="tool-1", engagement_id=engagement_id)]

    def list_pending_approvals(self) -> list[Row]:
        return []

    def decide_approval(self, *args: Any, **kwargs: Any) -> Row:
        return Row(id=args[0], status="approved")

    def record_evidence(self, **_: Any) -> Row:
        return Row(id="evidence-1")

    def list_evidence(self, engagement_id: str) -> list[Row]:
        return [Row(id="evidence-1", engagement_id=engagement_id)]

    def get_evidence_bytes(self, evidence_id: str) -> tuple[Row, bytes]:
        return Row(id=evidence_id), b"qa-evidence"

    def create_finding(self, **_: Any) -> Row:
        return Row(id="finding-1")

    def list_findings(self, engagement_id: str) -> list[Row]:
        return [Row(id="finding-1", engagement_id=engagement_id)]

    def list_audit_logs(self, limit: int = 100) -> list[Row]:
        return [Row(id="audit-1")]


@pytest.fixture(autouse=True)
def override_service() -> None:
    fake = FakeService()
    app.dependency_overrides[service_dep] = lambda: fake
    app.dependency_overrides[intake_service_dep] = lambda: fake
    yield
    app.dependency_overrides.clear()


@pytest.mark.contract
def test_health_and_stats_contract() -> None:
    client = TestClient(app)
    assert client.get("/health").status_code == 200
    stats = client.get("/stats")
    assert stats.status_code == 200
    assert stats.json()["engagements"] == 1


@pytest.mark.contract
def test_engagement_artifact_tool_and_report_contract() -> None:
    client = TestClient(app)
    assert client.post("/engagements", json={"engagement_id": "eng-qa", "name": "QA"}).status_code == 201
    assert client.get("/engagements").status_code == 200
    assert client.post("/engagements/eng-qa/targets", json={"target_ref": "app.authorized.test", "target_type": "domain"}).status_code == 201
    upload = client.post("/engagements/eng-qa/artifacts", files={"file": ("sample.bin", b"data", "application/octet-stream")})
    assert upload.status_code == 201
    assert client.get("/tools").status_code == 200
    assert client.get("/tools/status").status_code == 200
    proposed = client.post("/tool-calls", json={"engagement_id": "eng-qa", "actor": "qa", "tool": "ghidra", "operation": "analyze", "risk": "read_only", "arguments": {}})
    assert proposed.status_code == 201
    blocked = client.post("/tool-calls/tool-1/execute")
    assert blocked.status_code == 409
    assert blocked.json()["enqueue_endpoint"] == "/tool-calls/tool-1/enqueue"
    assert client.get("/engagements/eng-qa/report.md").status_code == 200


@pytest.mark.contract
def test_evidence_findings_approval_and_audit_contract() -> None:
    client = TestClient(app)
    assert client.get("/approvals/pending").json() == []
    assert client.post("/approvals/appr-1/decision", json={"approved": True, "decided_by": "qa"}).status_code == 200
    assert client.post("/engagements/eng-qa/evidence", json={"data": "hello", "media_type": "text/plain"}).status_code == 201
    assert client.get("/engagements/eng-qa/evidence").status_code == 200
    assert client.get("/evidence/evidence-1/download").content == b"qa-evidence"
    assert client.post("/engagements/eng-qa/findings", json={"title": "F", "description": "D"}).status_code == 201
    assert client.get("/engagements/eng-qa/findings").status_code == 200
    assert client.get("/audit").status_code == 200
