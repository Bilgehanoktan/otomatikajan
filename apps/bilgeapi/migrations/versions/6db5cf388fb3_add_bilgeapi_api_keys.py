"""add_bilgeapi_api_keys

Revision ID: 6db5cf388fb3
Revises: c4acb1b4c9f9
Create Date: 2026-06-06 01:43:46.387829
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '6db5cf388fb3'
down_revision: Union[str, None] = 'c4acb1b4c9f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('bilgeapi_api_keys',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('key_hash', sa.String(length=64), nullable=False),
    sa.Column('key_prefix', sa.String(length=16), nullable=False),
    sa.Column('key_fingerprint', sa.String(length=16), nullable=False),
    sa.Column('role', sa.String(length=32), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_by', sa.String(length=64), nullable=True),
    sa.Column('revoked_by', sa.String(length=64), nullable=True),
    sa.Column('revoke_reason', sa.Text(), nullable=True),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bilgeapi_api_keys_created_at'), 'bilgeapi_api_keys', ['created_at'], unique=False)
    op.create_index(op.f('ix_bilgeapi_api_keys_is_active'), 'bilgeapi_api_keys', ['is_active'], unique=False)
    op.create_index(op.f('ix_bilgeapi_api_keys_key_hash'), 'bilgeapi_api_keys', ['key_hash'], unique=True)
    op.create_index(op.f('ix_bilgeapi_api_keys_role'), 'bilgeapi_api_keys', ['role'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_bilgeapi_api_keys_role'), table_name='bilgeapi_api_keys')
    op.drop_index(op.f('ix_bilgeapi_api_keys_key_hash'), table_name='bilgeapi_api_keys')
    op.drop_index(op.f('ix_bilgeapi_api_keys_is_active'), table_name='bilgeapi_api_keys')
    op.drop_index(op.f('ix_bilgeapi_api_keys_created_at'), table_name='bilgeapi_api_keys')
    op.drop_table('bilgeapi_api_keys')
