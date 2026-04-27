"""add_policy_evolution_tables

Revision ID: 0d32eda31fe6
Revises: dfd787c12448
Create Date: 2026-04-27 01:08:53.626039
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import libs.db.base

revision: str = '0d32eda31fe6'
down_revision: Union[str, None] = 'dfd787c12448'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Phase 9 Tables ---
    op.create_table('governor_policy_evolutions',
        sa.Column('id', libs.db.base.GUID(), nullable=False),
        sa.Column('policy_key', sa.String(length=100), nullable=False),
        sa.Column('evolution_type', sa.Enum('RULE_CHANGE', 'VETO_PRIORITY_CHANGE', 'ESCALATION_POLICY_CHANGE', 'ARCHIVE_POLICY_CHANGE', 'REPLAY_POLICY_CHANGE', 'CONFLICT_RESOLUTION_CHANGE', name='policyevolutiontype'), nullable=False),
        sa.Column('old_value', postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
        sa.Column('proposed_value', postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), 'sqlite'), nullable=False),
        sa.Column('applied_value', postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('evidence_summary', postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('status', sa.Enum('PROPOSED', 'SIMULATED', 'APPROVED', 'APPLIED', 'REJECTED', 'ROLLED_BACK', name='policyevolutionstatus'), nullable=True),
        sa.Column('proposed_by', sa.String(length=100), nullable=True),
        sa.Column('approved_by', sa.String(length=100), nullable=True),
        sa.Column('rolled_back_from', libs.db.base.GUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('applied_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_governor_policy_evolutions_created_at'), 'governor_policy_evolutions', ['created_at'], unique=False)
    op.create_index(op.f('ix_governor_policy_evolutions_evolution_type'), 'governor_policy_evolutions', ['evolution_type'], unique=False)
    op.create_index(op.f('ix_governor_policy_evolutions_policy_key'), 'governor_policy_evolutions', ['policy_key'], unique=False)
    op.create_index(op.f('ix_governor_policy_evolutions_status'), 'governor_policy_evolutions', ['status'], unique=False)

    op.create_table('governor_policy_snapshots',
        sa.Column('id', libs.db.base.GUID(), nullable=False),
        sa.Column('snapshot_name', sa.String(length=200), nullable=False),
        sa.Column('policy_payload', postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), 'sqlite'), nullable=False),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_governor_policy_snapshots_created_at'), 'governor_policy_snapshots', ['created_at'], unique=False)

    op.create_table('governor_policy_simulations',
        sa.Column('id', libs.db.base.GUID(), nullable=False),
        sa.Column('evolution_id', libs.db.base.GUID(), nullable=False),
        sa.Column('simulation_window_days', sa.Integer(), nullable=True),
        sa.Column('sample_size', sa.Integer(), nullable=True),
        sa.Column('predicted_accuracy_delta', sa.Float(), nullable=True),
        sa.Column('predicted_false_positive_delta', sa.Float(), nullable=True),
        sa.Column('predicted_false_negative_delta', sa.Float(), nullable=True),
        sa.Column('predicted_escalation_delta', sa.Float(), nullable=True),
        sa.Column('predicted_latency_delta', sa.Float(), nullable=True),
        sa.Column('result_payload', postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['evolution_id'], ['governor_policy_evolutions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_governor_policy_simulations_evolution_id'), 'governor_policy_simulations', ['evolution_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_governor_policy_simulations_evolution_id'), table_name='governor_policy_simulations')
    op.drop_table('governor_policy_simulations')
    op.drop_index(op.f('ix_governor_policy_snapshots_created_at'), table_name='governor_policy_snapshots')
    op.drop_table('governor_policy_snapshots')
    op.drop_index(op.f('ix_governor_policy_evolutions_status'), table_name='governor_policy_evolutions')
    op.drop_index(op.f('ix_governor_policy_evolutions_policy_key'), table_name='governor_policy_evolutions')
    op.drop_index(op.f('ix_governor_policy_evolutions_evolution_type'), table_name='governor_policy_evolutions')
    op.drop_index(op.f('ix_governor_policy_evolutions_created_at'), table_name='governor_policy_evolutions')
    op.drop_table('governor_policy_evolutions')
    
    # Drop types if needed (usually handled by Alembic if they are only in these tables)
    # op.execute("DROP TYPE policyevolutiontype")
    # op.execute("DROP TYPE policyevolutionstatus")
