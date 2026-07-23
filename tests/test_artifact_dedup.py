from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest
from fastapi.testclient import TestClient

from intake.api import app
from intake.release_api import intake_service_dep
from intake.storage import sha256_bytes

pytestmark = pytest.mark.contract


@dataclass
class ArtifactRow:
    id: str = "artifact-existing"
    engagement_id: str = "eng-dedup"
    sha256: str = sha256_bytes(b"same-data")
    media_type: str = "application/octet-stream"
    size_bytes: int = len(b"same-data")
    storage_uri: str = "s3://bucket/existing"
    source: str = "api-upload"
    metadata_: dict[str, Any] = field(default_factory=dict)


class ExistingArtifactService:
    def __init__(self) -> None:
        self.session = self
        self.row = ArtifactRow()
        self.audit_events: list[dict[str, Any]] = []
        self.ingest_calls = 0

    def scalar(self, _statement: Any) -> ArtifactRow:
        return self.row

    def audit(self, **event: Any) -> None:
        self.audit_events.append(event)

    def commit(self) -> None:
        return None

    def ingest_artifact_bytes(self, **_: Any) -> ArtifactRow:
        self.ingest_calls += 1
        return self.row


@pytest.fixture
def service() -> ExistingArtifactService:
    fake = ExistingArtifactService()
    app.dependency_overrides[intake_service_dep] = lambda: fake
    yield fake
    app.dependency_overrides.clear()


def test_duplicate_upload_reuses_existing_record(service: ExistingArtifactService) -> None:
    response = TestClient(app).post(
        "/engagements/eng-dedup/artifacts",
        files={"file": ("sample.bin", b"same-data", "application/octet-stream")},
    )

    assert response.status_code == 201
    assert response.json()["id"] == "artifact-existing"
    assert service.ingest_calls == 0
    assert service.audit_events[0]["action"] == "artifact.reuse"
