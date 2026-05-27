"""CEO Engine and Model Router tables

Revision ID: 0004_ceo_and_router
Revises: 0003_standardize_status_names
Create Date: 2026-03-22 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0004_ceo_and_router"
down_revision = "0003_standardize_status_names"
branch_labels = None
depends_on = None

def upgrade() -> None:
    # ── improvement_opportunities ────────────────────────
    op.create_table(
        "improvement_opportunities",
        sa.Column("id",               postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_type",      sa.String(64), nullable=False),
        sa.Column("source_ref",       sa.String(256)),
        sa.Column("title",            sa.String(512), nullable=False),
        sa.Column("description",      sa.Text),
        sa.Column("severity",         sa.String(16),  server_default="medium"),
        sa.Column("category",         sa.String(64),  server_default="reliability"),
        sa.Column("impact_score",     sa.Float,       server_default="0.0"),
        sa.Column("urgency_score",    sa.Float,       server_default="0.0"),
        sa.Column("confidence_score", sa.Float,       server_default="0.0"),
        sa.Column("effort_score",     sa.Float,       server_default="0.0"),
        sa.Column("priority_score",   sa.Float,       server_default="0.0"),
        sa.Column("pattern_hash",     sa.String(64), nullable=True),
        sa.Column("evidence_detail",  sa.Text),
        sa.Column("status",           sa.String(32),  server_default="open"),
        sa.Column("created_at",       sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_improvement_opportunities_status", "improvement_opportunities", ["status"])
    op.create_index("ix_improvement_opportunities_priority", "improvement_opportunities", ["priority_score"])
    op.create_index("ix_improvement_opportunities_hash", "improvement_opportunities", ["pattern_hash"], unique=True)

    # ── ceo_suggested_tasks ──────────────────────────────
    op.create_table(
        "ceo_suggested_tasks",
        sa.Column("id",               postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("opportunity_id",   postgresql.UUID(as_uuid=True), sa.ForeignKey("improvement_opportunities.id", ondelete="SET NULL")),
        sa.Column("title",            sa.String(512), nullable=False),
        sa.Column("description",      sa.Text),
        sa.Column("priority",         sa.String(16),  server_default="medium"),
        sa.Column("owner_agent_hint", sa.String(64)),
        sa.Column("status",           sa.String(32),  server_default="suggested"),
        sa.Column("reasoning_summary", sa.Text),
        sa.Column("impact_projection", postgresql.JSONB, server_default="{}"),
        sa.Column("created_task_id",  postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at",       sa.DateTime(timezone=True), nullable=False),
    )

    # ── ceo_decisions ────────────────────────────────────
    op.create_table(
        "ceo_decisions",
        sa.Column("id",               postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("opportunity_id",   postgresql.UUID(as_uuid=True), sa.ForeignKey("improvement_opportunities.id", ondelete="CASCADE")),
        sa.Column("decision_type",    sa.String(64)),
        sa.Column("decision_summary", sa.Text),
        sa.Column("decision_source",  sa.String(64),  server_default="llm"),
        sa.Column("created_at",       sa.DateTime(timezone=True), nullable=False),
    )

    # ── ceo_performance_logs ─────────────────────────────
    op.create_table(
        "ceo_performance_logs",
        sa.Column("id",               postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("suggestion_id",    postgresql.UUID(as_uuid=True), sa.ForeignKey("ceo_suggested_tasks.id", ondelete="SET NULL")),
        sa.Column("project_id",       postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="SET NULL")),
        sa.Column("agent_id",         sa.String(64)),
        sa.Column("opportunity_type", sa.String(64)),
        sa.Column("success",          sa.Boolean,     server_default="true"),
        sa.Column("impact_score",     sa.Float,       server_default="0.0"),
        sa.Column("final_reasoning",  sa.Text),
        sa.Column("created_at",       sa.DateTime(timezone=True), nullable=False),
    )

    # ── model_router_logs ────────────────────────────────
    op.create_table(
        "model_router_logs",
        sa.Column("id",               postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("prompt_snippet",   sa.String(500)),
        sa.Column("agent_role",       sa.String(64), nullable=False),
        sa.Column("complexity",       sa.String(32), nullable=False),
        sa.Column("provider",         sa.String(64), nullable=False),
        sa.Column("model",            sa.String(128), nullable=False),
        sa.Column("estimated_cost_x", sa.Float,       server_default="1.0"),
        sa.Column("reason",           sa.String(512)),
        sa.Column("created_at",       sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_model_router_logs_role",     "model_router_logs", ["agent_role"])
    op.create_index("ix_model_router_logs_provider", "model_router_logs", ["provider"])
    op.create_index("ix_model_router_logs_created",  "model_router_logs", ["created_at"])

def downgrade() -> None:
    op.drop_table("model_router_logs")
    op.drop_table("ceo_performance_logs")
    op.drop_table("ceo_decisions")
    op.drop_table("ceo_suggested_tasks")
    op.drop_table("improvement_opportunities")
