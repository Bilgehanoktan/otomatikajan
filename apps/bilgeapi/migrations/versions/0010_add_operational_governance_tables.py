"""add operational governance tables

Revision ID: 0010_operational_gov
Revises: 0009_add_is_pilot_to_projects
Create Date: 2026-04-14 22:00:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '0010_operational_gov'
down_revision: str | None = '0009_add_is_pilot_to_projects'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    # 1. approval_requests table
    op.create_table('approval_requests',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('step_id', sa.String(length=128), nullable=True),
        sa.Column('request_type', sa.String(length=64), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('input_data', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=True),
        sa.Column('approver_id', sa.String(length=128), nullable=True),
        sa.Column('decision_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_approval_requests_created_at'), 'approval_requests', ['created_at'], unique=False)
    op.create_index(op.f('ix_approval_requests_project_id'), 'approval_requests', ['project_id'], unique=False)
    op.create_index(op.f('ix_approval_requests_status'), 'approval_requests', ['status'], unique=False)

    # 2. operational_incidents table
    op.create_table('operational_incidents',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('incident_type', sa.String(length=64), nullable=False),
        sa.Column('severity', sa.String(length=16), nullable=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=True),
        sa.Column('project_id', sa.UUID(), nullable=True),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_operational_incidents_created_at'), 'operational_incidents', ['created_at'], unique=False)
    op.create_index(op.f('ix_operational_incidents_incident_type'), 'operational_incidents', ['incident_type'], unique=False)
    op.create_index(op.f('ix_operational_incidents_status'), 'operational_incidents', ['status'], unique=False)

def downgrade() -> None:
    op.drop_table('operational_incidents')
    op.drop_table('approval_requests')
