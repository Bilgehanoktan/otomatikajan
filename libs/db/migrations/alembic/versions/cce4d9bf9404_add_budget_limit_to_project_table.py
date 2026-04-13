"""Add budget_limit to Project table

Revision ID: cce4d9bf9404
Revises: 0004_ceo_and_router
Create Date: 2026-03-25 23:22:52.058306
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'cce4d9bf9404'
down_revision: Union[str, None] = '0004_ceo_and_router'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("budget_limit", sa.Float(), server_default="0.0", nullable=False))


def downgrade() -> None:
    op.drop_column("projects", "budget_limit")
