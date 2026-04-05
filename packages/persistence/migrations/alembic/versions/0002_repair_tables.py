"""Add repair tables (Self-Repair Architecture - Faz 4)

Revision ID: 0002_repair_tables
Revises: 0001_initial_schema
Create Date: 2026-03-12 00:00:00.000000

Yeni tablolar:
- repair_incidents    : normalize edilmiş olay kayıtları
- repair_jobs         : pipeline durum makinesi
- repair_proposals    : PR önerileri (onay bekleniyor)
- repair_patch_logs   : geçmiş patch sonuçları (hafıza)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0002_repair_tables"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── repair_incidents ──────────────────────────────────
    op.create_table(
        "repair_incidents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("incident_id", sa.String(64), nullable=False, unique=True),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("service", sa.String(64), nullable=False),
        sa.Column("module", sa.String(128), nullable=False),
        sa.Column("symptom", sa.Text, nullable=False),
        sa.Column("stack_trace", sa.Text, server_default=""),
        sa.Column("suspected_files", postgresql.JSONB, server_default="[]"),
        sa.Column("failing_tests", postgresql.JSONB, server_default="[]"),
        sa.Column("reproduction_hint", sa.Text, server_default=""),
        sa.Column("context_data", postgresql.JSONB, server_default="{}"),
        sa.Column("occurrence_count", sa.Integer, server_default="1"),
        sa.Column("status", sa.String(32), server_default="open", nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_repair_incidents_incident_id", "repair_incidents", ["incident_id"])
    op.create_index("ix_repair_incidents_module_status", "repair_incidents", ["module", "status"])
    op.create_index("ix_repair_incidents_severity_status", "repair_incidents", ["severity", "status"])

    # ── repair_jobs ───────────────────────────────────────
    op.create_table(
        "repair_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", sa.String(64), nullable=False, unique=True),
        sa.Column("incident_id", sa.String(64), nullable=False),
        sa.Column("status", sa.String(64), nullable=False, server_default="new"),
        sa.Column("ticket_id", sa.String(64), nullable=True),
        sa.Column("plan_id", sa.String(64), nullable=True),
        sa.Column("validation_id", sa.String(64), nullable=True),
        sa.Column("pr_url", sa.String(512), nullable=True),
        sa.Column("branch_name", sa.String(256), nullable=True),
        sa.Column("diff", sa.Text, server_default=""),
        sa.Column("error_detail", sa.Text, server_default=""),
        sa.Column("history", postgresql.JSONB, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_repair_jobs_job_id", "repair_jobs", ["job_id"])
    op.create_index("ix_repair_jobs_incident_id", "repair_jobs", ["incident_id"])
    op.create_index("ix_repair_jobs_status_created", "repair_jobs", ["status", "created_at"])

    # ── repair_proposals ──────────────────────────────────
    op.create_table(
        "repair_proposals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pr_id", sa.String(64), nullable=False, unique=True),
        sa.Column("job_id", sa.String(64), nullable=False),
        sa.Column("incident_id", sa.String(64), nullable=False),
        sa.Column("branch_name", sa.String(256), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("body", sa.Text, server_default=""),
        sa.Column("diff", sa.Text, server_default=""),
        sa.Column("changed_files", postgresql.JSONB, server_default="[]"),
        sa.Column("risk_level", sa.String(16), server_default="low"),
        sa.Column("validation_summary", sa.Text, server_default=""),
        sa.Column("auto_merge", sa.Boolean, server_default="false", nullable=False),
        sa.Column("decision", sa.String(32), server_default="pending", nullable=False),
        sa.Column("decided_by", sa.String(128), server_default=""),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_repair_proposals_pr_id", "repair_proposals", ["pr_id"])
    op.create_index("ix_repair_proposals_job_id", "repair_proposals", ["job_id"])
    op.create_index("ix_repair_proposals_decision", "repair_proposals", ["decision"])

    # ── repair_patch_logs ─────────────────────────────────
    op.create_table(
        "repair_patch_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("record_id", sa.String(64), nullable=False, unique=True),
        sa.Column("job_id", sa.String(64), nullable=False),
        sa.Column("incident_id", sa.String(64), nullable=False),
        sa.Column("classification", sa.String(64), nullable=False),
        sa.Column("target_files", postgresql.JSONB, server_default="[]"),
        sa.Column("diff_size_lines", sa.Integer, server_default="0"),
        sa.Column("outcome", sa.String(32), nullable=False),
        sa.Column("confidence", sa.Integer, server_default="0"),
        sa.Column("validation_score", sa.Integer, server_default="0"),
        sa.Column("notes", sa.Text, server_default=""),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_repair_patch_logs_record_id", "repair_patch_logs", ["record_id"])
    op.create_index("ix_repair_patch_logs_job_id", "repair_patch_logs", ["job_id"])
    op.create_index("ix_repair_patch_logs_class_outcome", "repair_patch_logs", ["classification", "outcome"])


def downgrade() -> None:
    op.drop_table("repair_patch_logs")
    op.drop_table("repair_proposals")
    op.drop_table("repair_jobs")
    op.drop_table("repair_incidents")
