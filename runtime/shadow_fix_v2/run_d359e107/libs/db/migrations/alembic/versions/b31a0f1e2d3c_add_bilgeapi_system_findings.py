"""add_bilgeapi_system_findings

Revision ID: b31a0f1e2d3c
Revises: a29c4f83b2d1
Create Date: 2026-06-10
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "b31a0f1e2d3c"
down_revision = "a29c4f83b2d1"
branch_labels = None
depends_on = None


json_type = postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite")


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if _has_table("bilgeapi_system_findings"):
        return

    op.create_table(
        "bilgeapi_system_findings",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=True),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("source_id", sa.String(length=128), nullable=False),
        sa.Column("source_hash", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="OPEN"),
        sa.Column("evidence_summary", json_type, nullable=True),
        sa.Column("recommended_action", sa.Text(), nullable=True),
        sa.Column("human_gate_payload", json_type, nullable=True),
        sa.Column("occurrence_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("acknowledged_by", sa.String(length=64), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dismissed_by", sa.String(length=64), nullable=True),
        sa.Column("dismissed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by", sa.String(length=64), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("bilgeapi_research_id", sa.String(length=64), nullable=True),
        sa.Column("bilgeapi_proposal_id", sa.String(length=64), nullable=True),
        sa.Column("bilgeapi_pr_draft_id", sa.String(length=64), nullable=True),
        sa.Column("bilgeapi_verification_id", sa.String(length=64), nullable=True),
        sa.Column("bilgeapi_ledger_chain_id", sa.String(length=128), nullable=True),
        sa.Column("created_by", sa.String(length=64), nullable=True),
        sa.Column("correlation_id", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("source_hash", name="uq_bilgeapi_system_findings_source_hash"),
    )
    op.create_index("ix_bilgeapi_system_findings_tenant_id", "bilgeapi_system_findings", ["tenant_id"])
    op.create_index("ix_bilgeapi_system_findings_source_type", "bilgeapi_system_findings", ["source_type"])
    op.create_index("ix_bilgeapi_system_findings_source_id", "bilgeapi_system_findings", ["source_id"])
    op.create_index("ix_bilgeapi_system_findings_source_hash", "bilgeapi_system_findings", ["source_hash"], unique=True)
    op.create_index("ix_bilgeapi_system_findings_severity", "bilgeapi_system_findings", ["severity"])
    op.create_index("ix_bilgeapi_system_findings_status", "bilgeapi_system_findings", ["status"])
    op.create_index("ix_bilgeapi_system_findings_first_seen_at", "bilgeapi_system_findings", ["first_seen_at"])
    op.create_index("ix_bilgeapi_system_findings_last_seen_at", "bilgeapi_system_findings", ["last_seen_at"])
    op.create_index("ix_bilgeapi_system_findings_bilgeapi_research_id", "bilgeapi_system_findings", ["bilgeapi_research_id"])
    op.create_index("ix_bilgeapi_system_findings_bilgeapi_proposal_id", "bilgeapi_system_findings", ["bilgeapi_proposal_id"])
    op.create_index("ix_bilgeapi_system_findings_bilgeapi_pr_draft_id", "bilgeapi_system_findings", ["bilgeapi_pr_draft_id"])
    op.create_index("ix_bilgeapi_system_findings_bilgeapi_verification_id", "bilgeapi_system_findings", ["bilgeapi_verification_id"])
    op.create_index("ix_bilgeapi_system_findings_bilgeapi_ledger_chain_id", "bilgeapi_system_findings", ["bilgeapi_ledger_chain_id"])
    op.create_index("ix_bilgeapi_system_findings_correlation_id", "bilgeapi_system_findings", ["correlation_id"])
    op.create_index("ix_bilgeapi_system_findings_created_at", "bilgeapi_system_findings", ["created_at"])


def downgrade() -> None:
    if _has_table("bilgeapi_system_findings"):
        op.drop_table("bilgeapi_system_findings")
