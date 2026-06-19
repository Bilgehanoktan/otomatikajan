"""add_pr_draft_and_verification_tables

Revision ID: c8033461793d
Revises: d67ccf6e6920
Create Date: 2026-06-07 01:05:54.952786
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'c8033461793d'
down_revision: Union[str, None] = 'd67ccf6e6920'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    # 1. Create bilgeapi_pr_drafts if it doesn't exist
    if 'bilgeapi_pr_drafts' not in tables:
        op.create_table('bilgeapi_pr_drafts',
            sa.Column('id', sa.String(length=64), nullable=False),
            sa.Column('proposal_id', sa.String(length=64), sa.ForeignKey('bilgeapi_improvement_proposals.id'), nullable=False),
            sa.Column('provider', sa.String(length=32), nullable=False),
            sa.Column('status', sa.String(length=32), nullable=False),
            sa.Column('github_pr_url', sa.String(length=512), nullable=True),
            sa.Column('branch_name', sa.String(length=256), nullable=True),
            sa.Column('title', sa.String(length=256), nullable=False),
            sa.Column('body', sa.Text(), nullable=False),
            sa.Column('evidence_hash', sa.String(length=64), nullable=True),
            sa.Column('risk_level', sa.String(length=32), nullable=False),
            sa.Column('risk_flags', postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
            sa.Column('created_by', sa.String(length=64), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_bilgeapi_pr_drafts_created_at'), 'bilgeapi_pr_drafts', ['created_at'], unique=False)
        op.create_index(op.f('ix_bilgeapi_pr_drafts_proposal_id'), 'bilgeapi_pr_drafts', ['proposal_id'], unique=False)
        op.create_index(op.f('ix_bilgeapi_pr_drafts_status'), 'bilgeapi_pr_drafts', ['status'], unique=False)

    # 2. Create bilgeapi_pr_verifications if it doesn't exist
    if 'bilgeapi_pr_verifications' not in tables:
        op.create_table('bilgeapi_pr_verifications',
            sa.Column('id', sa.String(length=64), nullable=False),
            sa.Column('pr_draft_id', sa.String(length=64), sa.ForeignKey('bilgeapi_pr_drafts.id'), nullable=False),
            sa.Column('proposal_id', sa.String(length=64), sa.ForeignKey('bilgeapi_improvement_proposals.id'), nullable=False),
            sa.Column('status', sa.String(length=32), nullable=False),
            sa.Column('review_score', sa.Float(), nullable=False),
            sa.Column('review_decision', sa.String(length=32), nullable=False),
            sa.Column('risk_level', sa.String(length=32), nullable=False),
            sa.Column('risk_flags', postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
            sa.Column('affected_files', postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
            sa.Column('mutation_detected', sa.Boolean(), nullable=False),
            sa.Column('test_files_present', sa.Boolean(), nullable=False),
            sa.Column('patch_size_lines', sa.Integer(), nullable=False),
            sa.Column('test_plan', postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
            sa.Column('rollback_plan', sa.Text(), nullable=True),
            sa.Column('verification_report', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_bilgeapi_pr_verifications_created_at'), 'bilgeapi_pr_verifications', ['created_at'], unique=False)
        op.create_index(op.f('ix_bilgeapi_pr_verifications_pr_draft_id'), 'bilgeapi_pr_verifications', ['pr_draft_id'], unique=False)
        op.create_index(op.f('ix_bilgeapi_pr_verifications_proposal_id'), 'bilgeapi_pr_verifications', ['proposal_id'], unique=False)
        op.create_index(op.f('ix_bilgeapi_pr_verifications_status'), 'bilgeapi_pr_verifications', ['status'], unique=False)


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if 'bilgeapi_pr_verifications' in tables:
        op.drop_index(op.f('ix_bilgeapi_pr_verifications_status'), table_name='bilgeapi_pr_verifications')
        op.drop_index(op.f('ix_bilgeapi_pr_verifications_proposal_id'), table_name='bilgeapi_pr_verifications')
        op.drop_index(op.f('ix_bilgeapi_pr_verifications_pr_draft_id'), table_name='bilgeapi_pr_verifications')
        op.drop_index(op.f('ix_bilgeapi_pr_verifications_created_at'), table_name='bilgeapi_pr_verifications')
        op.drop_table('bilgeapi_pr_verifications')

    if 'bilgeapi_pr_drafts' in tables:
        op.drop_index(op.f('ix_bilgeapi_pr_drafts_status'), table_name='bilgeapi_pr_drafts')
        op.drop_index(op.f('ix_bilgeapi_pr_drafts_proposal_id'), table_name='bilgeapi_pr_drafts')
        op.drop_index(op.f('ix_bilgeapi_pr_drafts_created_at'), table_name='bilgeapi_pr_drafts')
        op.drop_table('bilgeapi_pr_drafts')

