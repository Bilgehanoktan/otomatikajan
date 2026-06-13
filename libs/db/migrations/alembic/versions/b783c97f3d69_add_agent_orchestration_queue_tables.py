"""add_agent_orchestration_queue_tables

Revision ID: b783c97f3d69
Revises: 971644420bb9
Create Date: 2026-06-13 00:59:54.488205
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'b783c97f3d69'
down_revision: Union[str, None] = '971644420bb9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('bilgeapi_agent_tasks',
    sa.Column('task_id', sa.String(length=64), nullable=False),
    sa.Column('source', sa.String(length=64), nullable=False),
    sa.Column('agent_role', sa.String(length=64), nullable=False),
    sa.Column('action_type', sa.String(length=64), nullable=False),
    sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
    sa.Column('risk_level', sa.String(length=32), nullable=False),
    sa.Column('priority_score', sa.Float(), nullable=False),
    sa.Column('status', sa.String(length=32), nullable=False),
    sa.Column('idempotency_key', sa.String(length=128), nullable=True),
    sa.Column('attempt_count', sa.Integer(), nullable=False),
    sa.Column('max_attempts', sa.Integer(), nullable=False),
    sa.Column('decision_id', sa.String(length=64), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['decision_id'], ['bilgeapi_autonomy_decisions.id'], ),
    sa.PrimaryKeyConstraint('task_id')
    )
    op.create_index(op.f('ix_bilgeapi_agent_tasks_created_at'), 'bilgeapi_agent_tasks', ['created_at'], unique=False)
    op.create_index(op.f('ix_bilgeapi_agent_tasks_idempotency_key'), 'bilgeapi_agent_tasks', ['idempotency_key'], unique=True)
    op.create_index(op.f('ix_bilgeapi_agent_tasks_status'), 'bilgeapi_agent_tasks', ['status'], unique=False)
    
    op.create_table('bilgeapi_agent_orchestration_runs',
    sa.Column('run_id', sa.String(length=64), nullable=False),
    sa.Column('task_id', sa.String(length=64), nullable=False),
    sa.Column('status', sa.String(length=32), nullable=False),
    sa.Column('execution_summary', sa.Text(), nullable=True),
    sa.Column('evidence_ledger_hash', sa.String(length=128), nullable=True),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['task_id'], ['bilgeapi_agent_tasks.task_id'], ),
    sa.PrimaryKeyConstraint('run_id')
    )
    op.create_index(op.f('ix_bilgeapi_agent_orchestration_runs_task_id'), 'bilgeapi_agent_orchestration_runs', ['task_id'], unique=False)
    
    op.create_table('bilgeapi_agent_task_leases',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('task_id', sa.String(length=64), nullable=False),
    sa.Column('lease_owner', sa.String(length=128), nullable=False),
    sa.Column('lease_expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('acquired_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['task_id'], ['bilgeapi_agent_tasks.task_id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bilgeapi_agent_task_leases_task_id'), 'bilgeapi_agent_task_leases', ['task_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_bilgeapi_agent_task_leases_task_id'), table_name='bilgeapi_agent_task_leases')
    op.drop_table('bilgeapi_agent_task_leases')
    op.drop_index(op.f('ix_bilgeapi_agent_orchestration_runs_task_id'), table_name='bilgeapi_agent_orchestration_runs')
    op.drop_table('bilgeapi_agent_orchestration_runs')
    op.drop_index(op.f('ix_bilgeapi_agent_tasks_status'), table_name='bilgeapi_agent_tasks')
    op.drop_index(op.f('ix_bilgeapi_agent_tasks_idempotency_key'), table_name='bilgeapi_agent_tasks')
    op.drop_index(op.f('ix_bilgeapi_agent_tasks_created_at'), table_name='bilgeapi_agent_tasks')
    op.drop_table('bilgeapi_agent_tasks')
