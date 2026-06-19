"""add_repair_agent_promotions

Revision ID: 3b517c6cb58a
Revises: 32b9c1d4e5f6
Create Date: 2026-06-11 19:50:05.110959
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '3b517c6cb58a'
down_revision: Union[str, None] = '32b9c1d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

json_type = postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite")

def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()

def upgrade() -> None:
    if not _has_table("repair_agent_promotions"):
        op.create_table(
            "repair_agent_promotions",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("promotion_id", sa.String(length=64), nullable=False),
            sa.Column("run_id", sa.String(length=64), nullable=False),
            sa.Column("artifact_type", sa.String(length=32), nullable=False),
            sa.Column("sandbox_artifact_path", sa.String(length=512), nullable=False),
            sa.Column("target_repo_path", sa.String(length=512), nullable=False),
            sa.Column("artifact_hash", sa.String(length=128), nullable=False),
            sa.Column("manifest_hash", sa.String(length=128), nullable=True),
            sa.Column("verified_artifact_hash", sa.String(length=128), nullable=True),
            sa.Column("approved_artifact_hash", sa.String(length=128), nullable=True),
            sa.Column("promoted_artifact_hash", sa.String(length=128), nullable=True),
            sa.Column("target_path_hash", sa.String(length=128), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="PENDING_VERIFICATION"),
            sa.Column("verification_score", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("verification_details", json_type, nullable=True),
            sa.Column("approved_by", sa.String(length=128), nullable=True),
            sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("promoted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("ledger_event_hash", sa.String(length=128), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("promotion_id", name="uq_repair_agent_promotions_promotion_id"),
        )
        op.create_index("ix_repair_agent_promotions_promotion_id", "repair_agent_promotions", ["promotion_id"], unique=False)
        op.create_index("ix_repair_agent_promotions_run_id", "repair_agent_promotions", ["run_id"], unique=False)
        op.create_index("ix_repair_agent_promotions_status", "repair_agent_promotions", ["status"], unique=False)
        op.create_index("ix_repair_agent_promotions_ledger_event_hash", "repair_agent_promotions", ["ledger_event_hash"], unique=False)

def downgrade() -> None:
    if _has_table("repair_agent_promotions"):
        op.drop_table("repair_agent_promotions")
