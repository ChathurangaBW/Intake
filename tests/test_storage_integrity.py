from __future__ import annotations

import pytest

from intake.storage import EvidenceStore, sha256_bytes

pytestmark = pytest.mark.unit


def make_store(data: bytes) -> EvidenceStore:
    store = EvidenceStore.__new__(EvidenceStore)
    store.get_bytes = lambda _digest: data  # type: ignore[method-assign]
    return store


def test_integrity_verification_accepts_matching_digest_and_size() -> None:
    data = b"intake-evidence"
    digest = sha256_bytes(data)
    result = make_store(data).verify(digest, len(data))

    assert result.valid
    assert result.digest_matches
    assert result.size_matches


def test_integrity_verification_detects_digest_and_size_mismatch() -> None:
    result = make_store(b"changed").verify("0" * 64, 99)

    assert not result.valid
    assert not result.digest_matches
    assert not result.size_matches
