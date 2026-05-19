"""add evolution lineage tables

Revision ID: 0013_evolution_tables
Revises: 0012_add_fleet_economic_fields
Create Date: 2026-04-17 04:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '0013_evolution_tables'
down_revision: str | None = '0012_add_fleet_economic_fields'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    # 1. decision_lineage table
    op.create_table('decision_lineage',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('decision_type', sa.String(), nullable=False),
        sa.Column('component_name', sa.String(), nullable=False),
        sa.Column('parent_id', sa.UUID(), nullable=True),
        sa.Column('root_id', sa.UUID(), nullable=True),
        sa.Column('trigger_event', sa.JSON(), nullable=True),
        sa.Column('rationale', sa.String(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('integrity_hash', sa.String(length=64), nullable=True),
        sa.Column('meta_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['parent_id'], ['decision_lineage.id'], ),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True
    )
    op.create_index(op.f('ix_decision_lineage_integrity_hash'), 'decision_lineage', ['integrity_hash'], unique=False)

    # 2. policy_evolution table
    op.create_table('policy_evolution',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('policy_key', sa.String(), nullable=False),
        sa.Column('version', sa.String(), nullable=False),
        sa.Column('previous_value', sa.JSON(), nullable=True),
        sa.Column('new_value', sa.JSON(), nullable=False),
        sa.Column('change_reason', sa.String(), nullable=True),
        sa.Column('author_id', sa.String(), nullable=True),
        sa.Column('decision_id', sa.UUID(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['decision_id'], ['decision_lineage.id'], ),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True
    )

def downgrade() -> None:
    op.drop_table('policy_evolution')
    op.drop_table('decision_lineage')
