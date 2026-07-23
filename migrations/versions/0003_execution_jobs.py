"""add durable execution jobs

Revision ID: 0003_execution_jobs
Revises: 0002_audit_logs
Create Date: 2026-07-23
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003_execution_jobs"
down_revision = "0002_audit_logs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_tool_calls_status", "tool_calls", ["status"])
    op.create_table(
        "execution_jobs",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tool_call_id", sa.String(length=64), sa.ForeignKey("tool_calls.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("leased_by", sa.String(length=128), nullable=True),
        sa.Column("leased_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_requested", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("result_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("tool_call_id", name="uq_execution_job_tool_call"),
    )
    op.create_index("ix_execution_jobs_tool_call_id", "execution_jobs", ["tool_call_id"])
    op.create_index("ix_execution_jobs_status", "execution_jobs", ["status"])
    op.create_index("ix_execution_jobs_priority", "execution_jobs", ["priority"])
    op.create_index("ix_execution_jobs_leased_until", "execution_jobs", ["leased_until"])


def downgrade() -> None:
    op.drop_index("ix_execution_jobs_leased_until", table_name="execution_jobs")
    op.drop_index("ix_execution_jobs_priority", table_name="execution_jobs")
    op.drop_index("ix_execution_jobs_status", table_name="execution_jobs")
    op.drop_index("ix_execution_jobs_tool_call_id", table_name="execution_jobs")
    op.drop_table("execution_jobs")
    op.drop_index("ix_tool_calls_status", table_name="tool_calls")
