from __future__ import annotations

from html import escape

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from intake.models import Artifact, AuditLog, Engagement, Evidence, Finding, Target, ToolCall


def _count(session: Session, model: type[object], engagement_id: str | None = None) -> int:
    stmt = select(func.count()).select_from(model)
    if engagement_id is not None and hasattr(model, "engagement_id"):
        stmt = stmt.where(model.engagement_id == engagement_id)  # type: ignore[attr-defined]
    return int(session.scalar(stmt) or 0)


def render_dashboard(session: Session) -> str:
    engagements = list(session.scalars(select(Engagement).order_by(Engagement.created_at.desc()).limit(25)))
    rows = []
    for engagement in engagements:
        rows.append(
            "<tr>"
            f"<td><a href='/ui/engagements/{escape(engagement.id)}'>{escape(engagement.id)}</a></td>"
            f"<td>{escape(engagement.name)}</td>"
            f"<td>{escape(engagement.status)}</td>"
            f"<td>{_count(session, Target, engagement.id)}</td>"
            f"<td>{_count(session, Artifact, engagement.id)}</td>"
            f"<td>{_count(session, ToolCall, engagement.id)}</td>"
            f"<td>{_count(session, Finding, engagement.id)}</td>"
            "</tr>"
        )

    return _page(
        "Intake Dashboard",
        f"""
        <h1>Intake</h1>
        <p>Policy-controlled authorized security automation runtime.</p>
        <section class="cards">
          <div><strong>{_count(session, Engagement)}</strong><span>Engagements</span></div>
          <div><strong>{_count(session, Artifact)}</strong><span>Artifacts</span></div>
          <div><strong>{_count(session, Evidence)}</strong><span>Evidence</span></div>
          <div><strong>{_count(session, ToolCall)}</strong><span>Tool calls</span></div>
        </section>
        <h2>Recent engagements</h2>
        <table>
          <thead><tr><th>ID</th><th>Name</th><th>Status</th><th>Targets</th><th>Artifacts</th><th>Tool calls</th><th>Findings</th></tr></thead>
          <tbody>{''.join(rows) or '<tr><td colspan="7">No engagements yet.</td></tr>'}</tbody>
        </table>
        <p><a href="/docs">OpenAPI docs</a></p>
        """,
    )


def render_engagement(session: Session, engagement_id: str) -> str:
    engagement = session.get(Engagement, engagement_id)
    if engagement is None:
        return _page("Not found", "<h1>Engagement not found</h1>")

    tool_calls = list(
        session.scalars(
            select(ToolCall)
            .where(ToolCall.engagement_id == engagement_id)
            .order_by(ToolCall.created_at.desc())
            .limit(50)
        )
    )
    findings = list(
        session.scalars(
            select(Finding)
            .where(Finding.engagement_id == engagement_id)
            .order_by(Finding.created_at.desc())
            .limit(50)
        )
    )
    audit = list(
        session.scalars(
            select(AuditLog)
            .where(AuditLog.subject.like(f"%{engagement_id}%"))
            .order_by(AuditLog.timestamp.desc())
            .limit(50)
        )
    )

    return _page(
        f"Engagement {escape(engagement_id)}",
        f"""
        <p><a href="/ui">← Dashboard</a></p>
        <h1>{escape(engagement.name)}</h1>
        <p><strong>ID:</strong> {escape(engagement.id)} | <strong>Status:</strong> {escape(engagement.status)}</p>
        <section class="cards">
          <div><strong>{_count(session, Target, engagement_id)}</strong><span>Targets</span></div>
          <div><strong>{_count(session, Artifact, engagement_id)}</strong><span>Artifacts</span></div>
          <div><strong>{_count(session, Evidence, engagement_id)}</strong><span>Evidence</span></div>
          <div><strong>{_count(session, Finding, engagement_id)}</strong><span>Findings</span></div>
        </section>
        <h2>Tool calls</h2>
        <table><thead><tr><th>ID</th><th>Tool</th><th>Operation</th><th>Risk</th><th>Status</th></tr></thead><tbody>
          {''.join(f'<tr><td>{escape(row.id)}</td><td>{escape(row.tool)}</td><td>{escape(row.operation)}</td><td>{escape(row.risk)}</td><td>{escape(row.status)}</td></tr>' for row in tool_calls) or '<tr><td colspan="5">No tool calls.</td></tr>'}
        </tbody></table>
        <h2>Findings</h2>
        <table><thead><tr><th>Title</th><th>Severity</th><th>Status</th><th>Verification</th></tr></thead><tbody>
          {''.join(f'<tr><td>{escape(row.title)}</td><td>{escape(row.severity)}</td><td>{escape(row.status)}</td><td>{escape(row.verification_status)}</td></tr>' for row in findings) or '<tr><td colspan="4">No findings.</td></tr>'}
        </tbody></table>
        <h2>Audit</h2>
        <table><thead><tr><th>Time</th><th>Actor</th><th>Action</th><th>Outcome</th></tr></thead><tbody>
          {''.join(f'<tr><td>{row.timestamp.isoformat()}</td><td>{escape(row.actor)}</td><td>{escape(row.action)}</td><td>{escape(row.outcome)}</td></tr>' for row in audit) or '<tr><td colspan="4">No audit events.</td></tr>'}
        </tbody></table>
        <p><a href="/engagements/{escape(engagement_id)}/report.md">Markdown report</a></p>
        """,
    )


def _page(title: str, body: str) -> str:
    return f"""
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>{escape(title)}</title>
      <style>
        body {{ font-family: system-ui, sans-serif; margin: 2rem; background: #101418; color: #e8eef5; }}
        a {{ color: #9fd3ff; }}
        table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
        th, td {{ border: 1px solid #314150; padding: 0.55rem; text-align: left; }}
        th {{ background: #18222c; }}
        .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 1rem; margin: 1rem 0; }}
        .cards div {{ background: #18222c; border: 1px solid #314150; border-radius: 8px; padding: 1rem; }}
        .cards strong {{ display: block; font-size: 2rem; }}
        .cards span {{ color: #a8b3bf; }}
      </style>
    </head>
    <body>{body}</body>
    </html>
    """
