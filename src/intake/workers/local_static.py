from __future__ import annotations

import re
from collections import Counter

from sqlalchemy.orm import Session

from intake.models import Artifact, Evidence
from intake.storage import EvidenceStore
from intake.workers.static import StaticWorkerClient, StaticWorkerRequest, StaticWorkerResult

_PRINTABLE_RE = re.compile(rb"[\x20-\x7e]{4,}")


def _extract_ascii_strings(data: bytes, *, limit: int = 100) -> list[str]:
    strings: list[str] = []
    for match in _PRINTABLE_RE.finditer(data):
        try:
            strings.append(match.group(0).decode("utf-8", errors="replace"))
        except UnicodeDecodeError:
            continue
        if len(strings) >= limit:
            break
    return strings


def _magic_summary(data: bytes) -> dict[str, object]:
    prefix = data[:16]
    file_type = "unknown"
    if data.startswith(b"MZ"):
        file_type = "pe-or-dos-family"
    elif data.startswith(b"\x7fELF"):
        file_type = "elf"
    elif data.startswith(b"PK\x03\x04"):
        file_type = "zip-family"
    elif data.startswith(b"\xcf\xfa\xed\xfe") or data.startswith(b"\xca\xfe\xba\xbe"):
        file_type = "mach-o-family"
    return {"file_type_hint": file_type, "first_16_bytes_hex": prefix.hex()}


class LocalStaticWorkerClient(StaticWorkerClient):
    """Safe built-in static worker.

    This worker performs metadata and string extraction only. It does not execute
    the artifact, invoke a shell, or perform network activity. It gives the app a
    usable default worker while preserving the later Ghidra/Rizin worker boundary.
    """

    def __init__(self, session: Session, evidence_store: EvidenceStore | None = None) -> None:
        self.session = session
        self.evidence_store = evidence_store or EvidenceStore()

    async def submit(self, request: StaticWorkerRequest) -> StaticWorkerResult:
        artifact = self.session.get(Artifact, request.artifact_id)
        if artifact is None:
            return StaticWorkerResult(
                worker_id=request.worker_id,
                tool_call_id=request.tool_call_id,
                status="not_found",
                summary=f"Artifact not found: {request.artifact_id}",
            )

        data = self.evidence_store.get_bytes(artifact.sha256)
        strings = _extract_ascii_strings(data, limit=100)
        byte_counts = Counter(data)
        top_bytes = [
            {"byte": byte, "count": count}
            for byte, count in byte_counts.most_common(10)
        ]
        report = {
            "artifact_id": artifact.id,
            "sha256": artifact.sha256,
            "size_bytes": artifact.size_bytes,
            "media_type": artifact.media_type,
            "profile": request.profile,
            "magic": _magic_summary(data),
            "string_count_sampled": len(strings),
            "strings_sample": strings,
            "top_bytes": top_bytes,
            "worker_boundary": "local-static-read-only",
        }
        report_bytes = (str(report) + "\n").encode("utf-8")
        stored = self.evidence_store.put_bytes(report_bytes, media_type="application/json")
        evidence = Evidence(
            engagement_id=artifact.engagement_id,
            tool_call_id=request.tool_call_id if request.tool_call_id != "pending" else None,
            sha256=stored.sha256,
            media_type="application/json",
            size_bytes=stored.size_bytes,
            storage_uri=stored.storage_uri,
            summary=f"Static metadata report for artifact {artifact.id}",
            metadata_={"worker_id": request.worker_id, "profile": request.profile},
        )
        self.session.add(evidence)
        self.session.commit()
        self.session.refresh(evidence)

        return StaticWorkerResult(
            worker_id=request.worker_id,
            tool_call_id=request.tool_call_id,
            status="completed",
            summary=f"Read-only static metadata analysis completed for {artifact.id}",
            evidence=[{"id": evidence.id, "sha256": evidence.sha256, "storage_uri": evidence.storage_uri}],
        )
