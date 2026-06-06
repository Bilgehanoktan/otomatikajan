"""add_quota_columns

Revision ID: 408c3b9b3b51
Revises: 6db5cf388fb3
Create Date: 2026-06-06 01:57:49.224992
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '408c3b9b3b51'
down_revision: Union[str, None] = '6db5cf388fb3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('bilgeapi_api_keys', schema=None) as batch_op:
        batch_op.add_column(sa.Column('quota_daily', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('quota_monthly', sa.Integer(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('bilgeapi_api_keys', schema=None) as batch_op:
        batch_op.drop_column('quota_monthly')
        batch_op.drop_column('quota_daily')
