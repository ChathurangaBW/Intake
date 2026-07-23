from __future__ import annotations

import pytest

from intake.web import render_dashboard, render_engagement


@pytest.mark.contract
def test_operator_console_exposes_product_workflows() -> None:
    html = render_dashboard(None)  # type: ignore[arg-type]

    assert "Intake Operator Console" in html
    assert "createEngagement" in html
    assert "uploadArtifact" in html
    assert "proposeTool" in html
    assert "approvalTable" in html
    assert "downloadEngagementExport" in html
    assert "/ops/readiness" in html
    assert "/ops/evidence/verify" in html
    assert "No unrestricted shell" not in html


@pytest.mark.contract
def test_engagement_console_seeds_active_engagement() -> None:
    html = render_engagement(None, "eng-console")  # type: ignore[arg-type]

    assert "const initialEngagement = \"eng-console\";" in html
    assert "activeEngagement" in html
