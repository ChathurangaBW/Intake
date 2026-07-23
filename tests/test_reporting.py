import pytest

from intake.reporting import ReportFinding, render_markdown_report


@pytest.mark.unit
def test_empty_report_is_explicit() -> None:
    report = render_markdown_report(engagement_id="eng-1", findings=[])

    assert "No verified findings" in report


@pytest.mark.unit
def test_report_includes_evidence_ids() -> None:
    report = render_markdown_report(
        engagement_id="eng-1",
        findings=[
            ReportFinding(
                title="Example",
                severity="low",
                status="draft",
                verification_status="verified",
                description="Description",
                evidence_ids=["ev-1"],
            )
        ],
    )

    assert "Example" in report
    assert "ev-1" in report
