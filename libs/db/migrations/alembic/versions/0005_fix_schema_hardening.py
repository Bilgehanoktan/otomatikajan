"""add agent_id to llm_cost_logs and sync schema

Revision ID: 0005_fix_schema_hardening
Revises: cce4d9bf9404
Create Date: 2026-03-26 23:45:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '0005_fix_schema_hardening'
down_revision: str | None = 'cce4d9bf9404'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. LLM Cost Logs: agent_id and error_type missing
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = [c['name'] for c in inspector.get_columns("llm_cost_logs")]
    if "agent_id" not in cols:
        op.add_column("llm_cost_logs", sa.Column("agent_id", sa.String(length=64), nullable=False, server_default="system"))
    if "error_type" not in cols:
        op.add_column("llm_cost_logs", sa.Column("error_type", sa.String(length=64), nullable=True))

    # 2. Webhook Subscriptions sync
    wh_cols = [c['name'] for c in inspector.get_columns("webhook_subscriptions")]
    if "owner_id" not in wh_cols:
        op.add_column('webhook_subscriptions', sa.Column('owner_id', sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True))
    if "is_active" not in wh_cols:
        op.add_column('webhook_subscriptions', sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False))

    # 3. Api Metrics sync (fixing the UUID cast issue and adding missing columns)
    am_cols = inspector.get_columns("api_metrics")
    am_col_names = [c['name'] for c in am_cols]

    # Fix user_id type
    for c in am_cols:
        if c['name'] == 'user_id' and not isinstance(c['type'], postgresql.UUID):
            op.execute('ALTER TABLE api_metrics ALTER COLUMN user_id DROP DEFAULT')
            op.execute("ALTER TABLE api_metrics ALTER COLUMN user_id TYPE UUID USING NULLIF(user_id, '')::uuid")
            op.execute('ALTER TABLE api_metrics ALTER COLUMN user_id SET DEFAULT NULL')

    # Add missing hardening columns
    if "ip_address" not in am_col_names:
        op.add_column("api_metrics", sa.Column("ip_address", sa.String(length=45), nullable=True))
    if "error_type" not in am_col_names:
        op.add_column("api_metrics", sa.Column("error_type", sa.String(length=64), nullable=True))

def downgrade() -> None:
    op.drop_column("llm_cost_logs", "agent_id")
    op.drop_column("llm_cost_logs", "error_type")
    op.drop_column('webhook_subscriptions', 'is_active')
    op.drop_column('webhook_subscriptions', 'owner_id')
    op.drop_column('api_metrics', 'ip_address')
    op.drop_column('api_metrics', 'error_type')
