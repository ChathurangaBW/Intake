from pathlib import Path

from intake.evidence import make_evidence_record


def test_make_evidence_record(tmp_path: Path) -> None:
    sample = tmp_path / "sample.bin"
    sample.write_bytes(b"intake")

    record = make_evidence_record(sample, media_type="application/octet-stream", source_tool="test")

    assert record.evidence_id.startswith("sha256:")
    assert record.size_bytes == 6
    assert record.source_tool == "test"
