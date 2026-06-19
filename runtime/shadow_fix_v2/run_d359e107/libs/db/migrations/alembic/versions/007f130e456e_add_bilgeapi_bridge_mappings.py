"""add bilgeapi_bridge_mappings

Revision ID: 007f130e456e
Revises: 62451c6b30ed
Create Date: 2026-06-10 19:34:37.536906
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '007f130e456e'
down_revision: Union[str, None] = '62451c6b30ed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('bilgeapi_bridge_mappings',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('source_type', sa.String(length=64), nullable=False),
    sa.Column('source_id', sa.String(length=128), nullable=False),
    sa.Column('bilgeapi_finding_id', sa.String(length=64), nullable=True),
    sa.Column('bilgeapi_research_id', sa.String(length=64), nullable=True),
    sa.Column('bilgeapi_proposal_id', sa.String(length=64), nullable=True),
    sa.Column('bilgeapi_pr_draft_id', sa.String(length=64), nullable=True),
    sa.Column('bilgeapi_verification_id', sa.String(length=64), nullable=True),
    sa.Column('bilgeapi_ledger_chain_id', sa.String(length=128), nullable=True),
    sa.Column('status', sa.String(length=32), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('source_type', 'source_id', name='uq_bilgeapi_bridge_source')
    )
    op.create_index(op.f('ix_bilgeapi_bridge_mappings_bilgeapi_finding_id'), 'bilgeapi_bridge_mappings', ['bilgeapi_finding_id'], unique=False)
    op.create_index(op.f('ix_bilgeapi_bridge_mappings_bilgeapi_ledger_chain_id'), 'bilgeapi_bridge_mappings', ['bilgeapi_ledger_chain_id'], unique=False)
    op.create_index(op.f('ix_bilgeapi_bridge_mappings_bilgeapi_pr_draft_id'), 'bilgeapi_bridge_mappings', ['bilgeapi_pr_draft_id'], unique=False)
    op.create_index(op.f('ix_bilgeapi_bridge_mappings_bilgeapi_proposal_id'), 'bilgeapi_bridge_mappings', ['bilgeapi_proposal_id'], unique=False)
    op.create_index(op.f('ix_bilgeapi_bridge_mappings_bilgeapi_research_id'), 'bilgeapi_bridge_mappings', ['bilgeapi_research_id'], unique=False)
    op.create_index(op.f('ix_bilgeapi_bridge_mappings_bilgeapi_verification_id'), 'bilgeapi_bridge_mappings', ['bilgeapi_verification_id'], unique=False)
    op.create_index(op.f('ix_bilgeapi_bridge_mappings_created_at'), 'bilgeapi_bridge_mappings', ['created_at'], unique=False)
    op.create_index(op.f('ix_bilgeapi_bridge_mappings_source_id'), 'bilgeapi_bridge_mappings', ['source_id'], unique=False)
    op.create_index(op.f('ix_bilgeapi_bridge_mappings_source_type'), 'bilgeapi_bridge_mappings', ['source_type'], unique=False)
    op.create_index(op.f('ix_bilgeapi_bridge_mappings_status'), 'bilgeapi_bridge_mappings', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_bilgeapi_bridge_mappings_status'), table_name='bilgeapi_bridge_mappings')
    op.drop_index(op.f('ix_bilgeapi_bridge_mappings_source_type'), table_name='bilgeapi_bridge_mappings')
    op.drop_index(op.f('ix_bilgeapi_bridge_mappings_source_id'), table_name='bilgeapi_bridge_mappings')
    op.drop_index(op.f('ix_bilgeapi_bridge_mappings_created_at'), table_name='bilgeapi_bridge_mappings')
    op.drop_index(op.f('ix_bilgeapi_bridge_mappings_bilgeapi_verification_id'), table_name='bilgeapi_bridge_mappings')
    op.drop_index(op.f('ix_bilgeapi_bridge_mappings_bilgeapi_research_id'), table_name='bilgeapi_bridge_mappings')
    op.drop_index(op.f('ix_bilgeapi_bridge_mappings_bilgeapi_proposal_id'), table_name='bilgeapi_bridge_mappings')
    op.drop_index(op.f('ix_bilgeapi_bridge_mappings_bilgeapi_pr_draft_id'), table_name='bilgeapi_bridge_mappings')
    op.drop_index(op.f('ix_bilgeapi_bridge_mappings_bilgeapi_ledger_chain_id'), table_name='bilgeapi_bridge_mappings')
    op.drop_index(op.f('ix_bilgeapi_bridge_mappings_bilgeapi_finding_id'), table_name='bilgeapi_bridge_mappings')
    op.drop_table('bilgeapi_bridge_mappings')
