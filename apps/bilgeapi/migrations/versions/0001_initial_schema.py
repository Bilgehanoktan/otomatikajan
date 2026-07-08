"""Ilk schema migrasyonu — tüm tablolar

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-03-10 00:00:00.000000

Bu migration create_all() ile oluşturulan şemayı versiyonlu hale getirir.
Production'da: alembic upgrade head
Geri alma:      alembic downgrade base
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # ── pgvector extension (vector adıyla kurulur) ────────
    if op.get_bind().dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ── users ────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id",              postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email",           sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active",       sa.Boolean, server_default="true"),
        sa.Column("is_admin",        sa.Boolean, server_default="false"),
        sa.Column("created_at",      sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ── refresh_tokens ───────────────────────────────────
    op.create_table(
        "refresh_tokens",
        sa.Column("id",         postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id",    postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("token",      sa.Text, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked",    sa.Boolean, server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_refresh_tokens_token", "refresh_tokens", ["token"], unique=True)

    # ── projects ─────────────────────────────────────────
    op.create_table(
        "projects",
        sa.Column("id",             postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_id",       postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title",          sa.String(500), nullable=False),
        sa.Column("description",    sa.Text,  server_default=""),
        sa.Column("status",         sa.String(32),  server_default="pending", nullable=False),
        sa.Column("report",         sa.Text,  server_default=""),
        sa.Column("job_id",         sa.String(64), nullable=True),
        sa.Column("total_cost",     sa.Float, server_default="0"),
        sa.Column("source",         sa.String(32),  server_default="api", nullable=False),
        sa.Column("priority",       sa.String(16),  server_default="medium", nullable=False),
        sa.Column("progress_pct",   sa.Integer, server_default="0"),
        sa.Column("tags",           sa.JSON, server_default="[]"),
        sa.Column("deadline",       sa.DateTime(timezone=True), nullable=True),
        sa.Column("assigned_agent", sa.String(64), server_default=""),
        sa.Column("error_detail",   sa.Text, server_default=""),
        sa.Column("retry_count",    sa.Integer, server_default="0"),
        sa.Column("notes",          sa.Text, server_default=""),
        sa.Column("cancelled_at",   sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_by",   sa.String(128), server_default=""),
        sa.Column("created_at",     sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at",     sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at",   sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_projects_status",     "projects", ["status"])
    op.create_index("ix_projects_source",     "projects", ["source"])
    op.create_index("ix_projects_priority",   "projects", ["priority"])
    op.create_index("ix_projects_created_at", "projects", ["created_at"])
    op.create_index("ix_projects_job_id",     "projects", ["job_id"])

    # ── subtasks ─────────────────────────────────────────
    op.create_table(
        "subtasks",
        sa.Column("id",            postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id",    postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("projects.id", ondelete="CASCADE")),
        sa.Column("agent_id",      sa.String(64), nullable=False),
        sa.Column("prompt",        sa.Text, nullable=False),
        sa.Column("result",        sa.Text, server_default=""),
        sa.Column("status",        sa.String(32), server_default="pending", nullable=False),
        sa.Column("attempts",      sa.Integer, server_default="0"),
        sa.Column("recovered",     sa.Boolean, server_default="false"),
        sa.Column("llm_provider",  sa.String(64), server_default=""),
        sa.Column("input_tokens",  sa.Integer, server_default="0"),
        sa.Column("output_tokens", sa.Integer, server_default="0"),
        sa.Column("cost_usd",      sa.Float,   server_default="0"),
        sa.Column("latency_s",     sa.Float,   server_default="0"),
        sa.Column("quality_score", sa.Float, nullable=True),
        sa.Column("created_at",    sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at",  sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_subtasks_project_id", "subtasks", ["project_id"])
    op.create_index("ix_subtasks_agent_id",   "subtasks", ["agent_id"])
    op.create_index("ix_subtasks_status",     "subtasks", ["status"])

    # ── llm_cost_logs ────────────────────────────────────
    op.create_table(
        "llm_cost_logs",
        sa.Column("id",            postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id",    postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=True),
        sa.Column("subtask_id",    postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("provider",      sa.String(64), nullable=False),
        sa.Column("model",         sa.String(128), server_default=""),
        sa.Column("input_tokens",  sa.Integer, server_default="0"),
        sa.Column("output_tokens", sa.Integer, server_default="0"),
        sa.Column("cost_usd",      sa.Float, server_default="0"),
        sa.Column("latency_s",     sa.Float, server_default="0"),
        sa.Column("success",       sa.Boolean, server_default="true"),
        sa.Column("error",         sa.Text, server_default=""),
        sa.Column("created_at",    sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_llm_cost_logs_provider",   "llm_cost_logs", ["provider"])
    op.create_index("ix_llm_cost_logs_created_at", "llm_cost_logs", ["created_at"])

    # ── domain_event_logs ────────────────────────────────
    op.create_table(
        "domain_event_logs",
        sa.Column("id",         postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("agent_id",   sa.String(64),  server_default=""),
        sa.Column("severity",   sa.String(32),  server_default="info"),
        sa.Column("phase",      sa.String(64),  server_default=""),
        sa.Column("message",    sa.Text, server_default=""),
        sa.Column("payload",    sa.JSON, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_domain_event_logs_event_type", "domain_event_logs", ["event_type"])
    op.create_index("ix_domain_event_logs_created_at", "domain_event_logs", ["created_at"])
    op.create_index("ix_domain_event_logs_severity",   "domain_event_logs", ["severity"])

    # ── agent_health_logs ────────────────────────────────
    op.create_table(
        "agent_health_logs",
        sa.Column("id",           postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id",     sa.String(64), nullable=False),
        sa.Column("health_score", sa.Float, server_default="1.0"),
        sa.Column("event",        sa.String(64), server_default=""),
        sa.Column("detail",       sa.Text, server_default=""),
        sa.Column("created_at",   sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_agent_health_logs_agent_id",   "agent_health_logs", ["agent_id"])
    op.create_index("ix_agent_health_logs_created_at", "agent_health_logs", ["created_at"])

    # ── webhook_subscriptions ────────────────────────────
    op.create_table(
        "webhook_subscriptions",
        sa.Column("id",         postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("url",        sa.Text, nullable=False),
        sa.Column("events",     sa.JSON, server_default="[]"),
        sa.Column("secret",     sa.String(256), server_default=""),
        sa.Column("active",     sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # ── rate_limit_counters ──────────────────────────────
    op.create_table(
        "rate_limit_counters",
        sa.Column("id",         postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("key",        sa.String(255), nullable=False),
        sa.Column("count",      sa.Integer, server_default="0"),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("window_end",   sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_rate_limit_counters_key",        "rate_limit_counters", ["key"])
    op.create_index("ix_rate_limit_counters_window_end", "rate_limit_counters", ["window_end"])

    # ── task_logs ────────────────────────────────────────
    op.create_table(
        "task_logs",
        sa.Column("id",         postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("projects.id", ondelete="CASCADE")),
        sa.Column("level",      sa.String(16), server_default="info"),
        sa.Column("event",      sa.String(128), server_default=""),
        sa.Column("message",    sa.Text, server_default=""),
        sa.Column("agent_id",   sa.String(64), server_default=""),
        sa.Column("payload",    sa.JSON, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_task_logs_project_id", "task_logs", ["project_id"])
    op.create_index("ix_task_logs_created_at", "task_logs", ["created_at"])

    # ── api_metrics ──────────────────────────────────────
    op.create_table(
        "api_metrics",
        sa.Column("id",          postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("endpoint",    sa.String(255), nullable=False),
        sa.Column("method",      sa.String(16),  server_default=""),
        sa.Column("status_code", sa.Integer,     server_default="0"),
        sa.Column("response_ms",  sa.Float,       server_default="0"),
        sa.Column("user_id",     sa.String(128), server_default=""),
        sa.Column("trace_id",    sa.String(64),  server_default=""),
        sa.Column("sampled",     sa.Boolean,     server_default="true"),
        sa.Column("created_at",  sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_api_metrics_endpoint",   "api_metrics", ["endpoint"])
    op.create_index("ix_api_metrics_created_at", "api_metrics", ["created_at"])
    op.create_index("ix_api_metrics_status_code","api_metrics", ["status_code"])

    # ── telegram_users ───────────────────────────────────
    op.create_table(
        "telegram_users",
        sa.Column("id",          postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger, nullable=False),
        sa.Column("username",    sa.String(128), server_default=""),
        sa.Column("is_authorized", sa.Boolean, server_default="false"),
        sa.Column("is_admin",    sa.Boolean, server_default="false"),
        sa.Column("created_at",  sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen",   sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_telegram_users_telegram_id", "telegram_users", ["telegram_id"], unique=True)

    # ── telegram_command_logs ────────────────────────────
    op.create_table(
        "telegram_command_logs",
        sa.Column("id",          postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger, nullable=False),
        sa.Column("command",     sa.String(128), nullable=False),
        sa.Column("args",        sa.Text, server_default=""),
        sa.Column("response",    sa.Text, server_default=""),
        sa.Column("success",     sa.Boolean, server_default="true"),
        sa.Column("created_at",  sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_telegram_command_logs_telegram_id", "telegram_command_logs", ["telegram_id"])

    # ── memories ─────────────────────────────────────────
    op.create_table(
        "memories",
        sa.Column("id",          postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id",    sa.String(64), nullable=False),
        sa.Column("content",     sa.Text, nullable=False),
        sa.Column("category",    sa.String(64), server_default="general"),
        sa.Column("importance",  sa.Float, server_default="1.0"),
        sa.Column("metadata_",   sa.JSON, server_default="{}"),
        sa.Column("expires_at",  sa.DateTime(timezone=True), nullable=True),
        sa.Column("tags",        sa.JSON, server_default="[]"),
        sa.Column("project_id",  sa.String(64), server_default=""),
        sa.Column("created_at",  sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_memories_agent_id",   "memories", ["agent_id"])
    op.create_index("ix_memories_created_at", "memories", ["created_at"])
    op.create_index("ix_memories_project_id", "memories", ["project_id"])


def downgrade() -> None:
    # Ters sırada sil (FK kısıtları nedeniyle)
    op.drop_table("memories")
    op.drop_table("telegram_command_logs")
    op.drop_table("telegram_users")
    op.drop_table("api_metrics")
    op.drop_table("task_logs")
    op.drop_table("rate_limit_counters")
    op.drop_table("webhook_subscriptions")
    op.drop_table("agent_health_logs")
    op.drop_table("domain_event_logs")
    op.drop_table("llm_cost_logs")
    op.drop_table("subtasks")
    op.drop_table("projects")
    op.drop_table("refresh_tokens")
    op.drop_table("users")
