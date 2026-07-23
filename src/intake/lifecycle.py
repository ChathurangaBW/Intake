from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from intake.models import AuditLog, Evidence, Finding
from intake.release_schemas import FindingUpdate
from intake.services import NotFoundError
from intake.storage import EvidenceStore, IntegrityResult


class LifecycleService:
    """Integrity and review lifecycle operations that sit above core CRUD."""

    def __init__(self, session: Session, *, evidence_store: EvidenceStore | None = None) -> None:
        self.session = session
        self._evidence_store = evidence_store

    @property
    def evidence_store(self) -> EvidenceStore:
        if self._evidence_store is None:
            self._evidence_store = EvidenceStore()
        return self._evidence_store

    def verify_evidence(self, evidence_id: str, *, actor: str) -> tuple[Evidence, IntegrityResult]:
        evidence = self.session.get(Evidence, evidence_id)
        if evidence is None:
            raise NotFoundError(f"unknown evidence: {evidence_id}")
        result = self.evidence_store.verify(evidence.sha256, evidence.size_bytes)
        self.session.add(
            AuditLog(
                actor=actor,
                action="evidence.verify",
                subject=evidence.id,
                outcome="valid" if result.valid else "invalid",
                metadata_={
                    "expected_sha256": result.expected_sha256,
                    "actual_sha256": result.actual_sha256,
                    "expected_size_bytes": result.expected_size_bytes,
                    "actual_size_bytes": result.actual_size_bytes,
                },
            )
        )
        self.session.commit()
        return evidence, result

    def update_finding(self, finding_id: str, payload: FindingUpdate, *, actor: str) -> Finding:
        finding = self.session.get(Finding, finding_id)
        if finding is None:
            raise NotFoundError(f"unknown finding: {finding_id}")

        changes: dict[str, Any] = {}
        for field_name, value in payload.model_dump(exclude_none=True).items():
            old_value = getattr(finding, field_name)
            if old_value != value:
                setattr(finding, field_name, value)
                changes[field_name] = {"from": old_value, "to": value}

        self.session.add(
            AuditLog(
                actor=actor,
                action="finding.update",
                subject=finding.id,
                outcome="success",
                metadata_={"changes": changes},
            )
        )
        self.session.commit()
        self.session.refresh(finding)
        return finding
