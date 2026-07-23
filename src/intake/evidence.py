from __future__ import annotations

import hashlib
from pathlib import Path

from intake.schemas import EvidenceRecord


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def make_evidence_record(path: Path, *, media_type: str, source_tool: str) -> EvidenceRecord:
    file_hash = sha256_file(path)
    return EvidenceRecord(
        evidence_id=f"sha256:{file_hash}",
        sha256=file_hash,
        media_type=media_type,
        size_bytes=path.stat().st_size,
        source_tool=source_tool,
        metadata={"filename": path.name},
    )
