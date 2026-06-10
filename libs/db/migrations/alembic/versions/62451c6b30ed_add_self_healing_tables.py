"""add self healing tables

Revision ID: 62451c6b30ed
Revises: b31a0f1e2d3c
Create Date: 2026-06-10 18:43:27.865460
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = '62451c6b30ed'
down_revision: Union[str, None] = 'b31a0f1e2d3c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

json_type = postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite")


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if not _has_table("bilgeapi_remediation_runbooks"):
        op.create_table(
            "bilgeapi_remediation_runbooks",
            sa.Column("id", sa.String(length=64), primary_key=True),
            sa.Column("name", sa.String(length=128), nullable=False),
            sa.Column("action_type", sa.String(length=64), nullable=False),
            sa.Column("severity_allowed", sa.String(length=32), nullable=False),
            sa.Column("requires_human_gate", sa.Boolean(), default=True, nullable=False),
            sa.Column("enabled", sa.Boolean(), default=False, nullable=False),
            sa.Column("execution_mode", sa.String(length=32), default="MANUAL", nullable=False),
            sa.Column("max_attempts", sa.Integer(), default=2, nullable=False),
            sa.Column("cooldown_seconds", sa.Integer(), default=300, nullable=False),
            sa.Column("safety_notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("name", name="uq_bilgeapi_remediation_runbooks_name"),
        )

    if not _has_table("bilgeapi_remediation_attempts"):
        op.create_table(
            "bilgeapi_remediation_attempts",
            sa.Column("id", sa.String(length=64), primary_key=True),
            sa.Column("finding_id", sa.String(length=64), sa.ForeignKey("bilgeapi_system_findings.id"), nullable=False),
            sa.Column("runbook_id", sa.String(length=64), sa.ForeignKey("bilgeapi_remediation_runbooks.id"), nullable=True),
            sa.Column("action_type", sa.String(length=64), nullable=False),
            sa.Column("status", sa.String(length=32), default="PENDING", nullable=False),
            sa.Column("attempt_no", sa.Integer(), default=1, nullable=False),
            sa.Column("before_health", json_type, nullable=True),
            sa.Column("after_health", json_type, nullable=True),
            sa.Column("output_summary", sa.Text(), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("policy_decision", json_type, nullable=True),
            sa.Column("forbidden_actions_checked", json_type, nullable=True),
            sa.Column("ledger_chain_id", sa.String(length=128), nullable=True),
            sa.Column("created_by", sa.String(length=64), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_bilgeapi_remediation_attempts_finding_id", "bilgeapi_remediation_attempts", ["finding_id"])
        op.create_index("ix_bilgeapi_remediation_attempts_runbook_id", "bilgeapi_remediation_attempts", ["runbook_id"])
        op.create_index("ix_bilgeapi_remediation_attempts_status", "bilgeapi_remediation_attempts", ["status"])
        op.create_index("ix_bilgeapi_remediation_attempts_ledger_chain_id", "bilgeapi_remediation_attempts", ["ledger_chain_id"])


def downgrade() -> None:
    if _has_table("bilgeapi_remediation_attempts"):
        op.drop_table("bilgeapi_remediation_attempts")
    if _has_table("bilgeapi_remediation_runbooks"):
        op.drop_table("bilgeapi_remediation_runbooks")

