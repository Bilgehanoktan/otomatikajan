"""add_reviewer_feedback_and_patch_revisions

Revision ID: e1a49df5d6bb
Revises: c8033461793d
Create Date: 2026-06-07 10:10:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'e1a49df5d6bb'
down_revision: Union[str, None] = 'c8033461793d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    # 1. Create bilgeapi_pr_review_feedbacks if it doesn't exist
    if 'bilgeapi_pr_review_feedbacks' not in tables:
        op.create_table('bilgeapi_pr_review_feedbacks',
            sa.Column('id', sa.String(length=64), nullable=False),
            sa.Column('pr_draft_id', sa.String(length=64), sa.ForeignKey('bilgeapi_pr_drafts.id'), nullable=False),
            sa.Column('reviewer_id', sa.String(length=64), nullable=False),
            sa.Column('comment', sa.Text(), nullable=False),
            sa.Column('status', sa.String(length=32), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_bilgeapi_pr_review_feedbacks_created_at'), 'bilgeapi_pr_review_feedbacks', ['created_at'], unique=False)
        op.create_index(op.f('ix_bilgeapi_pr_review_feedbacks_pr_draft_id'), 'bilgeapi_pr_review_feedbacks', ['pr_draft_id'], unique=False)
        op.create_index(op.f('ix_bilgeapi_pr_review_feedbacks_status'), 'bilgeapi_pr_review_feedbacks', ['status'], unique=False)

    # 2. Create bilgeapi_patch_revisions if it doesn't exist
    if 'bilgeapi_patch_revisions' not in tables:
        op.create_table('bilgeapi_patch_revisions',
            sa.Column('id', sa.String(length=64), nullable=False),
            sa.Column('pr_draft_id', sa.String(length=64), sa.ForeignKey('bilgeapi_pr_drafts.id'), nullable=False),
            sa.Column('feedback_id', sa.String(length=64), sa.ForeignKey('bilgeapi_pr_review_feedbacks.id'), nullable=True),
            sa.Column('revision_number', sa.Integer(), nullable=False),
            sa.Column('revised_patch_code', sa.Text(), nullable=False),
            sa.Column('risk_analysis', postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
            sa.Column('risk_level', sa.String(length=32), nullable=False),
            sa.Column('verification_status', sa.String(length=32), nullable=False),
            sa.Column('created_by', sa.String(length=64), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('pr_draft_id', 'revision_number', name='uq_pr_draft_revision')
        )
        op.create_index(op.f('ix_bilgeapi_patch_revisions_created_at'), 'bilgeapi_patch_revisions', ['created_at'], unique=False)
        op.create_index(op.f('ix_bilgeapi_patch_revisions_pr_draft_id'), 'bilgeapi_patch_revisions', ['pr_draft_id'], unique=False)
        op.create_index(op.f('ix_bilgeapi_patch_revisions_verification_status'), 'bilgeapi_patch_revisions', ['verification_status'], unique=False)

    # 3. Add revision_id to bilgeapi_pr_verifications if it doesn't exist
    if 'bilgeapi_pr_verifications' in tables:
        columns = [col['name'] for col in inspector.get_columns('bilgeapi_pr_verifications')]
        if 'revision_id' not in columns:
            with op.batch_alter_table('bilgeapi_pr_verifications') as batch_op:
                batch_op.add_column(sa.Column('revision_id', sa.String(length=64), sa.ForeignKey('bilgeapi_patch_revisions.id'), nullable=True))
            op.create_index(op.f('ix_bilgeapi_pr_verifications_revision_id'), 'bilgeapi_pr_verifications', ['revision_id'], unique=False)


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if 'bilgeapi_pr_verifications' in tables:
        columns = [col['name'] for col in inspector.get_columns('bilgeapi_pr_verifications')]
        if 'revision_id' in columns:
            op.drop_index(op.f('ix_bilgeapi_pr_verifications_revision_id'), table_name='bilgeapi_pr_verifications')
            with op.batch_alter_table('bilgeapi_pr_verifications') as batch_op:
                batch_op.drop_column('revision_id')

    if 'bilgeapi_patch_revisions' in tables:
        op.drop_index(op.f('ix_bilgeapi_patch_revisions_verification_status'), table_name='bilgeapi_patch_revisions')
        op.drop_index(op.f('ix_bilgeapi_patch_revisions_pr_draft_id'), table_name='bilgeapi_patch_revisions')
        op.drop_index(op.f('ix_bilgeapi_patch_revisions_created_at'), table_name='bilgeapi_patch_revisions')
        op.drop_table('bilgeapi_patch_revisions')

    if 'bilgeapi_pr_review_feedbacks' in tables:
        op.drop_index(op.f('ix_bilgeapi_pr_review_feedbacks_status'), table_name='bilgeapi_pr_review_feedbacks')
        op.drop_index(op.f('ix_bilgeapi_pr_review_feedbacks_pr_draft_id'), table_name='bilgeapi_pr_review_feedbacks')
        op.drop_index(op.f('ix_bilgeapi_pr_review_feedbacks_created_at'), table_name='bilgeapi_pr_review_feedbacks')
        op.drop_table('bilgeapi_pr_review_feedbacks')
