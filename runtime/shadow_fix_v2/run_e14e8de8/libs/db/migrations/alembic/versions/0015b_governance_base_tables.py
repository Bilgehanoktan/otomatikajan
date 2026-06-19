"""create governance base tables

Revision ID: 0015b_gov_base
Revises: 0015_outcome_lineage
Create Date: 2026-04-26 13:00:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

import libs.db.base

revision: str = '0015b_gov_base'
down_revision: str | None = '0015_outcome_lineage'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    # 1. Create governor_cases table
    op.create_table('governor_cases',
        sa.Column('id', libs.db.base.GUID(), nullable=False),
        sa.Column('project_id', libs.db.base.GUID(), nullable=False),
        sa.Column('project_title', sa.String(length=255), nullable=True),
        sa.Column('project_status', sa.String(length=50), nullable=True),
        sa.Column('pending_reason', sa.String(length=100), nullable=False),
        sa.Column('risk_class', sa.String(length=20), nullable=False),
        sa.Column('risk_score', sa.Integer(), nullable=True),
        sa.Column('recommended_decision', sa.String(length=50), nullable=False),
        sa.Column('decision_reason_codes', postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
        sa.Column('has_open_incident', sa.Integer(), server_default='0', nullable=True),
        sa.Column('has_safety_lock', sa.Integer(), server_default='0', nullable=True),
        sa.Column('has_active_fingerprint', sa.Integer(), server_default='0', nullable=True),
        sa.Column('requires_prime', sa.Integer(), server_default='0', nullable=True),
        sa.Column('requires_quorum', sa.Integer(), server_default='0', nullable=True),
        sa.Column('missing_context', sa.Integer(), server_default='0', nullable=True),
        sa.Column('stale_seconds', sa.Integer(), server_default='0', nullable=True),
        sa.Column('snapshot_payload', postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_governor_cases_created_at'), 'governor_cases', ['created_at'], unique=False)
    op.create_index(op.f('ix_governor_cases_project_id'), 'governor_cases', ['project_id'], unique=False)

    # 2. Create governor_actions table
    op.create_table('governor_actions',
        sa.Column('id', libs.db.base.GUID(), nullable=False),
        sa.Column('case_id', libs.db.base.GUID(), nullable=True),
        sa.Column('project_id', libs.db.base.GUID(), nullable=False),
        sa.Column('action_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='pending', nullable=True),
        sa.Column('executed_by', sa.String(length=100), nullable=True),
        sa.Column('result_payload', postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_governor_actions_case_id'), 'governor_actions', ['case_id'], unique=False)
    op.create_index(op.f('ix_governor_actions_created_at'), 'governor_actions', ['created_at'], unique=False)
    op.create_index(op.f('ix_governor_actions_project_id'), 'governor_actions', ['project_id'], unique=False)

    # 3. Create governor_escalations table
    op.create_table('governor_escalations',
        sa.Column('id', libs.db.base.GUID(), nullable=False),
        sa.Column('case_id', libs.db.base.GUID(), nullable=True),
        sa.Column('project_id', libs.db.base.GUID(), nullable=False),
        sa.Column('escalation_type', sa.String(length=50), nullable=False),
        sa.Column('target_role', sa.String(length=50), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='open', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_governor_escalations_case_id'), 'governor_escalations', ['case_id'], unique=False)
    op.create_index(op.f('ix_governor_escalations_created_at'), 'governor_escalations', ['created_at'], unique=False)
    op.create_index(op.f('ix_governor_escalations_project_id'), 'governor_escalations', ['project_id'], unique=False)

def downgrade() -> None:
    op.drop_table('governor_escalations')
    op.drop_table('governor_actions')
    op.drop_table('governor_cases')
