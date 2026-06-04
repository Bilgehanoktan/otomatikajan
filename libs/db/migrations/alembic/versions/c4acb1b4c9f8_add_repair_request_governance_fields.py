"""add_repair_request_governance_fields

Revision ID: c4acb1b4c9f8
Revises: c4acb1b4c9f7
Create Date: 2026-06-04 21:10:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'c4acb1b4c9f8'
down_revision: Union[str, None] = 'c4acb1b4c9f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add columns to bilgeapi_repair_requests table
    op.add_column('bilgeapi_repair_requests', sa.Column('approval_required', sa.Boolean(), server_default=sa.text('1'), nullable=False))
    op.add_column('bilgeapi_repair_requests', sa.Column('rejection_reason', sa.Text(), nullable=True))
    op.add_column('bilgeapi_repair_requests', sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('bilgeapi_repair_requests', sa.Column('rejected_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('bilgeapi_repair_requests', 'rejected_at')
    op.drop_column('bilgeapi_repair_requests', 'approved_at')
    op.drop_column('bilgeapi_repair_requests', 'rejection_reason')
    op.drop_column('bilgeapi_repair_requests', 'approval_required')
