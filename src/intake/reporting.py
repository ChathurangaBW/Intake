from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ReportFinding:
    title: str
    severity: str
    status: str
    verification_status: str
    description: str
    evidence_ids: list[str] = field(default_factory=list)


def render_markdown_report(*, engagement_id: str, findings: list[ReportFinding]) -> str:
    lines = [f"# Intake Assessment Report: {engagement_id}", ""]
    if not findings:
        lines.extend(["No verified findings have been recorded.", ""])
        return "\n".join(lines)

    for finding in findings:
        lines.extend(
            [
                f"## {finding.title}",
                "",
                f"- Severity: `{finding.severity}`",
                f"- Status: `{finding.status}`",
                f"- Verification: `{finding.verification_status}`",
                "",
                finding.description,
                "",
                "Evidence:",
            ]
        )
        for evidence_id in finding.evidence_ids:
            lines.append(f"- `{evidence_id}`")
        lines.append("")
    return "\n".join(lines)
