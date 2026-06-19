"""add_api_key_tenant_id

Revision ID: 5d8a1c2b7e90
Revises: 408c3b9b3b51
Create Date: 2026-06-06 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "5d8a1c2b7e90"
down_revision: Union[str, None] = "408c3b9b3b51"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("bilgeapi_api_keys", schema=None) as batch_op:
        batch_op.add_column(sa.Column("tenant_id", sa.String(length=64), nullable=True))
        batch_op.create_index(batch_op.f("ix_bilgeapi_api_keys_tenant_id"), ["tenant_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("bilgeapi_api_keys", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_bilgeapi_api_keys_tenant_id"))
        batch_op.drop_column("tenant_id")
