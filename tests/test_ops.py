from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from intake.ops import audit_record, payload_sha256


@pytest.mark.unit
def test_payload_sha256_is_canonical() -> None:
    left = {"b": 2, "a": {"z": 1}}
    right = {"a": {"z": 1}, "b": 2}

    assert payload_sha256(left) == payload_sha256(right)


@pytest.mark.unit
def test_payload_sha256_changes_when_payload_changes() -> None:
    assert payload_sha256({"a": 1}) != payload_sha256({"a": 2})


@pytest.mark.unit
def test_audit_record_serializes_timestamp_and_metadata() -> None:
    row = SimpleNamespace(
        id="audit-1",
        timestamp=datetime(2026, 7, 23, tzinfo=UTC),
        actor="operator",
        action="ops.export",
        subject="eng-1",
        outcome="ok",
        metadata_={"format": "ndjson"},
    )

    record = audit_record(row)

    assert record["id"] == "audit-1"
    assert record["timestamp"].startswith("2026-07-23")
    assert record["metadata"] == {"format": "ndjson"}
