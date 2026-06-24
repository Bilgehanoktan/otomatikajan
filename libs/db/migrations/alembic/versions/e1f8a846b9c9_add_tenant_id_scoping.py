"""add_tenant_id_scoping

Revision ID: e1f8a846b9c9
Revises: b783c97f3d69
Create Date: 2026-06-22 01:10:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e1f8a846b9c9"
down_revision: Union[str, None] = "b783c97f3d69"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABLES_WITH_INDEXES = [
    # (table_name, list_of_composite_indexes_to_create)
    # Each composite index config: (index_name, [columns])
    ("bilgeapi_incidents", [
        ("ix_bilgeapi_incidents_tenant_id", ["tenant_id"]),
        ("ix_bilgeapi_incidents_tenant_created", ["tenant_id", "created_at"])
    ]),
    ("bilgeapi_diagnostic_runs", [
        ("ix_bilgeapi_diagnostic_runs_tenant_id", ["tenant_id"]),
        ("ix_bilgeapi_diagnostic_runs_tenant_created", ["tenant_id", "created_at"]),
        ("ix_bilgeapi_diagnostic_runs_tenant_status", ["tenant_id", "status"])
    ]),
    ("bilgeapi_findings", [
        ("ix_bilgeapi_findings_tenant_id", ["tenant_id"])
    ]),
    ("bilgeapi_recommendations", [
        ("ix_bilgeapi_recommendations_tenant_id", ["tenant_id"])
    ]),
    ("bilgeapi_repair_requests", [
        ("ix_bilgeapi_repair_requests_tenant_id", ["tenant_id"]),
        ("ix_bilgeapi_repair_requests_tenant_created", ["tenant_id", "created_at"]),
        ("ix_bilgeapi_repair_requests_tenant_approval", ["tenant_id", "approval_status"]),
        ("ix_bilgeapi_repair_requests_tenant_dispatch", ["tenant_id", "dispatch_status"])
    ]),
    ("bilgeapi_audit_events", [
        ("ix_bilgeapi_audit_events_tenant_id", ["tenant_id"]),
        ("ix_bilgeapi_audit_events_tenant_created", ["tenant_id", "created_at"])
    ]),
    ("bilgeapi_webhook_deliveries", [
        ("ix_bilgeapi_webhook_deliveries_tenant_id", ["tenant_id"]),
        ("ix_bilgeapi_webhook_deliveries_tenant_created", ["tenant_id", "created_at"]),
        ("ix_bilgeapi_webhook_deliveries_tenant_status", ["tenant_id", "delivery_status"])
    ]),
    ("bilgeapi_pr_drafts", [
        ("ix_bilgeapi_pr_drafts_tenant_id", ["tenant_id"]),
        ("ix_bilgeapi_pr_drafts_tenant_created", ["tenant_id", "created_at"])
    ]),
    ("bilgeapi_pr_verifications", [
        ("ix_bilgeapi_pr_verifications_tenant_id", ["tenant_id"])
    ]),
    ("bilgeapi_pr_review_feedbacks", [
        ("ix_bilgeapi_pr_review_feedbacks_tenant_id", ["tenant_id"])
    ]),
    ("bilgeapi_patch_revisions", [
        ("ix_bilgeapi_patch_revisions_tenant_id", ["tenant_id"])
    ]),
    ("bilgeapi_review_ledger_entries", [
        ("ix_bilgeapi_review_ledger_entries_tenant_id", ["tenant_id"]),
        ("ix_bilgeapi_review_ledger_entries_tenant_created", ["tenant_id", "created_at"])
    ]),
    ("bilgeapi_ai_patch_suggestions", [
        ("ix_bilgeapi_ai_patch_suggestions_tenant_id", ["tenant_id"])
    ]),
    ("bilgeapi_system_findings", [
        ("ix_bilgeapi_system_findings_tenant_id", ["tenant_id"]),
        ("ix_bilgeapi_system_findings_tenant_created", ["tenant_id", "created_at"])
    ]),
    ("bilgeapi_remediation_runbooks", [
        ("ix_bilgeapi_remediation_runbooks_tenant_id", ["tenant_id"])
    ]),
    ("bilgeapi_remediation_attempts", [
        ("ix_bilgeapi_remediation_attempts_tenant_id", ["tenant_id"]),
        ("ix_bilgeapi_remediation_attempts_tenant_created", ["tenant_id", "created_at"])
    ]),
    ("bilgeapi_autonomy_decisions", [
        ("ix_bilgeapi_autonomy_decisions_tenant_id", ["tenant_id"]),
        ("ix_bilgeapi_autonomy_decisions_tenant_created", ["tenant_id", "created_at"])
    ]),
]


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # 1. Add tenant_id column to all tables if not exists
    for table_name, index_list in TABLES_WITH_INDEXES:
        columns = [c["name"] for c in inspector.get_columns(table_name)]
        if "tenant_id" not in columns:
            with op.batch_alter_table(table_name, schema=None) as batch_op:
                batch_op.add_column(sa.Column("tenant_id", sa.String(length=64), nullable=True))
            
    # 2. Backfill existing records with 'default' tenant
    for table_name, _ in TABLES_WITH_INDEXES:
        op.execute(f"UPDATE {table_name} SET tenant_id = 'default' WHERE tenant_id IS NULL")

    # 3. Create indexes if they don't exist
    for table_name, index_list in TABLES_WITH_INDEXES:
        existing_indexes = [idx["name"] for idx in inspector.get_indexes(table_name)]
        with op.batch_alter_table(table_name, schema=None) as batch_op:
            for index_name, columns in index_list:
                if index_name not in existing_indexes:
                    batch_op.create_index(batch_op.f(index_name), columns, unique=False)


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # 1. Drop indexes if they exist
    for table_name, index_list in TABLES_WITH_INDEXES:
        existing_indexes = [idx["name"] for idx in inspector.get_indexes(table_name)]
        with op.batch_alter_table(table_name, schema=None) as batch_op:
            for index_name, _ in index_list:
                if index_name in existing_indexes:
                    batch_op.drop_index(batch_op.f(index_name))

    # 2. Drop tenant_id column if exists
    for table_name, _ in TABLES_WITH_INDEXES:
        columns = [c["name"] for c in inspector.get_columns(table_name)]
        if "tenant_id" in columns:
            with op.batch_alter_table(table_name, schema=None) as batch_op:
                batch_op.drop_column("tenant_id")

