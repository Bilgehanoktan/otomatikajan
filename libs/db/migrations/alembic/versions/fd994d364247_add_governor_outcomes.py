"""add_governor_outcomes

Revision ID: fd994d364247
Revises: 7ce444aee8f5
Create Date: 2026-04-27 00:31:06.610361
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

import libs.db.base

revision: str = 'fd994d364247'
down_revision: str | None = '7ce444aee8f5'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('governor_outcomes',
        sa.Column('id', libs.db.base.GUID(), nullable=False),
        sa.Column('case_id', libs.db.base.GUID(), nullable=True),
        sa.Column('project_id', libs.db.base.GUID(), nullable=False),
        sa.Column('action_id', libs.db.base.GUID(), nullable=True),
        sa.Column('decision', sa.String(length=64), nullable=False),
        sa.Column('final_outcome', sa.Enum('SUCCESS', 'FAILED', 'REVERSED', 'ESCALATED', 'NO_SIGNAL', name='governoroutcometype'), nullable=False),
        sa.Column('quality', sa.Enum('CORRECT', 'FALSE_POSITIVE', 'FALSE_NEGATIVE', 'PARTIAL', name='governordecisionquality'), nullable=False),
        sa.Column('was_successful', sa.Integer(), nullable=True),
        sa.Column('operator_overrode', sa.Integer(), nullable=True),
        sa.Column('operator_agreed', sa.Integer(), nullable=True),
        sa.Column('resolution_latency_seconds', sa.Integer(), nullable=True),
        sa.Column('reason_codes', postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
        sa.Column('snapshot_payload', postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_governor_outcomes_action_id'), 'governor_outcomes', ['action_id'], unique=False)
    op.create_index(op.f('ix_governor_outcomes_case_id'), 'governor_outcomes', ['case_id'], unique=False)
    op.create_index(op.f('ix_governor_outcomes_created_at'), 'governor_outcomes', ['created_at'], unique=False)
    op.create_index(op.f('ix_governor_outcomes_decision'), 'governor_outcomes', ['decision'], unique=False)
    op.create_index(op.f('ix_governor_outcomes_final_outcome'), 'governor_outcomes', ['final_outcome'], unique=False)
    op.create_index(op.f('ix_governor_outcomes_project_id'), 'governor_outcomes', ['project_id'], unique=False)
    op.create_index(op.f('ix_governor_outcomes_quality'), 'governor_outcomes', ['quality'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_governor_outcomes_quality'), table_name='governor_outcomes')
    op.drop_index(op.f('ix_governor_outcomes_project_id'), table_name='governor_outcomes')
    op.drop_index(op.f('ix_governor_outcomes_final_outcome'), table_name='governor_outcomes')
    op.drop_index(op.f('ix_governor_outcomes_decision'), table_name='governor_outcomes')
    op.drop_index(op.f('ix_governor_outcomes_created_at'), table_name='governor_outcomes')
    op.drop_index(op.f('ix_governor_outcomes_case_id'), table_name='governor_outcomes')
    op.drop_index(op.f('ix_governor_outcomes_action_id'), table_name='governor_outcomes')
    op.drop_table('governor_outcomes')
