"""add bilgeapi release checks

Revision ID: c4acb1b4c9f9
Revises: c4acb1b4c9f8
Create Date: 2026-06-04 22:20:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Text
from sqlalchemy.dialects import postgresql

revision: str = 'c4acb1b4c9f9'
down_revision: Union[str, None] = 'c4acb1b4c9f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'bilgeapi_release_checks',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('blockers', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
        sa.Column('warnings', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
        sa.Column('checked_modules', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
        sa.Column('checked_endpoints', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
        sa.Column('smoke_trace', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
        sa.Column('app_version', sa.String(length=64), nullable=True),
        sa.Column('git_sha', sa.String(length=64), nullable=True),
        sa.Column('environment', sa.String(length=64), nullable=True),
        sa.Column('triggered_by', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('bilgeapi_release_checks', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_bilgeapi_release_checks_created_at'), ['created_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_bilgeapi_release_checks_status'), ['status'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('bilgeapi_release_checks', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_bilgeapi_release_checks_status'))
        batch_op.drop_index(batch_op.f('ix_bilgeapi_release_checks_created_at'))
    op.drop_table('bilgeapi_release_checks')
