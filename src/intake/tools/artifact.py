from pathlib import Path

from pydantic import BaseModel, Field

from intake.evidence import make_evidence_record
from intake.schemas import EvidenceRecord


class IdentifyArtifactRequest(BaseModel):
    path: Path
    media_type: str = Field(default="application/octet-stream")


def identify_artifact(request: IdentifyArtifactRequest) -> EvidenceRecord:
    """Read-only artifact identification.

    This does not execute the artifact. Dynamic execution must be handled by a
    disposable VM worker after explicit policy approval.
    """
    if not request.path.exists() or not request.path.is_file():
        raise FileNotFoundError(str(request.path))
    return make_evidence_record(
        request.path,
        media_type=request.media_type,
        source_tool="artifact.identify",
    )
