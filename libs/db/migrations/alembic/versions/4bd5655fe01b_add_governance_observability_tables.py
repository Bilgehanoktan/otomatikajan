"""add_governance_observability_tables

Revision ID: 4bd5655fe01b
Revises: 0d32eda31fe6
Create Date: 2026-04-27 01:14:28.987102
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import libs.db.base

revision: str = '4bd5655fe01b'
down_revision: Union[str, None] = '0d32eda31fe6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Phase 10 Tables ---
    op.create_table('governor_alerts',
        sa.Column('id', libs.db.base.GUID(), nullable=False),
        sa.Column('alert_type', sa.Enum('DECISION_ACCURACY_DROP', 'FALSE_POSITIVE_SPIKE', 'FALSE_NEGATIVE_SPIKE', 'POLICY_CHURN_SPIKE', 'META_CONFLICT_RATE_SPIKE', 'REPLAY_SUCCESS_REGRESSION', 'DOMAIN_TIMEOUT_BURST', 'CIRCUIT_BREAKER_OPEN_RATE', 'FREEZE_MODE_DURATION', 'DRIFT_DETECTED', name='governoralerttype'), nullable=False),
        sa.Column('severity', sa.Enum('INFO', 'WARNING', 'HIGH', 'CRITICAL', name='governoralertseverity'), nullable=False),
        sa.Column('status', sa.Enum('OPEN', 'ACKNOWLEDGED', 'RESOLVED', 'SUPPRESSED', name='governoralertstatus'), nullable=True),
        sa.Column('domain', postgresql.ENUM('WORKFLOW', 'INCIDENT', 'APPROVAL', 'POLICY', 'REPAIR', 'META', name='governordomain', create_type=False), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('metric_value', sa.Float(), nullable=True),
        sa.Column('threshold_value', sa.Float(), nullable=True),
        sa.Column('evidence_payload', postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
        sa.Column('opened_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('owner_id', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_governor_alerts_alert_type'), 'governor_alerts', ['alert_type'], unique=False)
    op.create_index(op.f('ix_governor_alerts_domain'), 'governor_alerts', ['domain'], unique=False)
    op.create_index(op.f('ix_governor_alerts_opened_at'), 'governor_alerts', ['opened_at'], unique=False)
    op.create_index(op.f('ix_governor_alerts_severity'), 'governor_alerts', ['severity'], unique=False)
    op.create_index(op.f('ix_governor_alerts_status'), 'governor_alerts', ['status'], unique=False)

    op.create_table('governor_metric_aggregates',
        sa.Column('id', libs.db.base.GUID(), nullable=False),
        sa.Column('metric_key', sa.String(length=100), nullable=False),
        sa.Column('domain', postgresql.ENUM('WORKFLOW', 'INCIDENT', 'APPROVAL', 'POLICY', 'REPAIR', 'META', name='governordomain', create_type=False), nullable=True),
        sa.Column('window_minutes', sa.Integer(), nullable=True),
        sa.Column('sample_size', sa.Integer(), nullable=True),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('baseline_value', sa.Float(), nullable=True),
        sa.Column('delta_value', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_governor_metric_aggregates_created_at'), 'governor_metric_aggregates', ['created_at'], unique=False)
    op.create_index(op.f('ix_governor_metric_aggregates_domain'), 'governor_metric_aggregates', ['domain'], unique=False)
    op.create_index(op.f('ix_governor_metric_aggregates_metric_key'), 'governor_metric_aggregates', ['metric_key'], unique=False)

    op.create_table('governor_drifts',
        sa.Column('id', libs.db.base.GUID(), nullable=False),
        sa.Column('drift_type', sa.Enum('RISK_DRIFT', 'DECISION_DRIFT', 'DOMAIN_DISAGREEMENT_DRIFT', 'POLICY_DRIFT', 'LATENCY_DRIFT', name='governordrifttype'), nullable=False),
        sa.Column('domain', postgresql.ENUM('WORKFLOW', 'INCIDENT', 'APPROVAL', 'POLICY', 'REPAIR', 'META', name='governordomain', create_type=False), nullable=True),
        sa.Column('baseline_window_days', sa.Integer(), nullable=True),
        sa.Column('current_window_days', sa.Integer(), nullable=True),
        sa.Column('drift_score', sa.Float(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('evidence_payload', postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_governor_drifts_created_at'), 'governor_drifts', ['created_at'], unique=False)
    op.create_index(op.f('ix_governor_drifts_domain'), 'governor_drifts', ['domain'], unique=False)
    op.create_index(op.f('ix_governor_drifts_drift_type'), 'governor_drifts', ['drift_type'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_governor_drifts_drift_type'), table_name='governor_drifts')
    op.drop_index(op.f('ix_governor_drifts_domain'), table_name='governor_drifts')
    op.drop_index(op.f('ix_governor_drifts_created_at'), table_name='governor_drifts')
    op.drop_table('governor_drifts')
    op.drop_index(op.f('ix_governor_metric_aggregates_metric_key'), table_name='governor_metric_aggregates')
    op.drop_index(op.f('ix_governor_metric_aggregates_domain'), table_name='governor_metric_aggregates')
    op.drop_index(op.f('ix_governor_metric_aggregates_created_at'), table_name='governor_metric_aggregates')
    op.drop_table('governor_metric_aggregates')
    op.drop_index(op.f('ix_governor_alerts_status'), table_name='governor_alerts')
    op.drop_index(op.f('ix_governor_alerts_severity'), table_name='governor_alerts')
    op.drop_index(op.f('ix_governor_alerts_opened_at'), table_name='governor_alerts')
    op.drop_index(op.f('ix_governor_alerts_domain'), table_name='governor_alerts')
    op.drop_index(op.f('ix_governor_alerts_alert_type'), table_name='governor_alerts')
    op.drop_table('governor_alerts')
