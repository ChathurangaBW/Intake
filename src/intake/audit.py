from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    timestamp: datetime
    actor: str
    action: str
    subject: str
    outcome: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        actor: str,
        action: str,
        subject: str,
        outcome: str,
        metadata: dict[str, Any] | None = None,
    ) -> AuditEvent:
        return cls(
            event_id=str(uuid4()),
            timestamp=datetime.now(UTC),
            actor=actor,
            action=action,
            subject=subject,
            outcome=outcome,
            metadata=metadata or {},
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "actor": self.actor,
            "action": self.action,
            "subject": self.subject,
            "outcome": self.outcome,
            "metadata": self.metadata,
        }
