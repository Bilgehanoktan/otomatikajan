"""add updated_at to projects and sync subtasks

Revision ID: f002a05eadd5
Revises: 0007_skill_execution_logs
Create Date: 2026-03-29 08:17:51.382840
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'f002a05eadd5'
down_revision: Union[str, None] = '0007_skill_execution_logs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Projects: updated_at column is missing in DB but exists in Model
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = [c['name'] for c in inspector.get_columns("projects")]
    if "updated_at" not in cols:
        op.add_column("projects", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
    
    # 2. Subtasks: sync missing columns
    st_cols = [c['name'] for c in inspector.get_columns("subtasks")]
    if "updated_at" not in st_cols:
        op.add_column("subtasks", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
    if "cost_usd" not in st_cols:
        op.add_column("subtasks", sa.Column("cost_usd", sa.Float(), server_default="0", nullable=False))
    if "latency_s" not in st_cols:
        op.add_column("subtasks", sa.Column("latency_s", sa.Float(), server_default="0", nullable=False))

def downgrade() -> None:
    op.drop_column("projects", "updated_at")
    op.drop_column("subtasks", "updated_at")
    op.drop_column("subtasks", "cost_usd")
    op.drop_column("subtasks", "latency_s")
