from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ReportFinding:
    title: str
    severity: str
    status: str
    verification_status: str
    description: str
    evidence_ids: list[str] = field(default_factory=list)


def _engagement_id(engagement: Any | None, fallback: str | None) -> str:
    if fallback is not None:
        return fallback
    if engagement is None:
        return "unknown"
    return str(getattr(engagement, "id", "unknown"))


def _finding_value(finding: Any, name: str, default: str = "") -> str:
    return str(getattr(finding, name, default) or default)


def _finding_evidence_ids(finding: Any) -> list[str]:
    ids = getattr(finding, "evidence_ids", None)
    if ids is None:
        return []
    return [str(item) for item in ids]


def render_markdown_report(
    *,
    engagement: Any | None = None,
    engagement_id: str | None = None,
    findings: list[Any],
) -> str:
    eid = _engagement_id(engagement, engagement_id)
    lines = [f"# Intake Assessment Report: {eid}", ""]

    if engagement is not None:
        lines.extend(
            [
                "## Engagement",
                "",
                f"- Name: `{getattr(engagement, 'name', eid)}`",
                f"- Status: `{getattr(engagement, 'status', 'unknown')}`",
                f"- Classification: `{getattr(engagement, 'classification', 'unknown')}`",
                "",
            ]
        )

    if not findings:
        lines.extend(["## Findings", "", "No findings have been recorded.", ""])
        return "\n".join(lines)

    lines.extend(["## Findings", ""])
    for finding in findings:
        lines.extend(
            [
                f"### {_finding_value(finding, 'title', 'Untitled finding')}",
                "",
                f"- Severity: `{_finding_value(finding, 'severity', 'informational')}`",
                f"- Status: `{_finding_value(finding, 'status', 'draft')}`",
                f"- Verification: `{_finding_value(finding, 'verification_status', 'unverified')}`",
                "",
                _finding_value(finding, "description", "No description recorded."),
                "",
            ]
        )
        evidence_ids = _finding_evidence_ids(finding)
        if evidence_ids:
            lines.append("Evidence:")
            for evidence_id in evidence_ids:
                lines.append(f"- `{evidence_id}`")
            lines.append("")
    return "\n".join(lines)
