"""add fleet orchestra tables

Revision ID: 0016
Revises: e4a7b5d12345
Create Date: 2026-04-27 01:37:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0016'
down_revision = 'e4a7b5d12345'
branch_labels = None
depends_on = None

def upgrade():
    # 1. Fleet Clusters
    op.create_table(
        'fleet_clusters',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='ACTIVE'),
        sa.Column('region', sa.String(length=64), server_default='global'),
        sa.Column('budget_limit', sa.Float(), server_default='0.0'),
        sa.Column('current_budget_usage', sa.Float(), server_default='0.0'),
        sa.Column('max_parallel_projects', sa.Integer(), server_default='5'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )
    op.create_index('ix_fleet_clusters_status', 'fleet_clusters', ['status'])

    # 2. Agent Nodes
    op.create_table(
        'agent_nodes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('cluster_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('fleet_clusters.id', ondelete='SET NULL'), nullable=True),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('role', sa.String(length=32), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='IDLE'),
        sa.Column('trust_score', sa.Float(), server_default='1.0'),
        sa.Column('current_load', sa.Integer(), server_default='0'),
        sa.Column('max_concurrency', sa.Integer(), server_default='1'),
        sa.Column('last_heartbeat', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('project_scope', sa.String(length=256), nullable=True),
        sa.Column('cost_rate', sa.Float(), server_default='0.0'),
        sa.Column('capabilities', postgresql.JSONB(astext_type=sa.Text()), server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )
    op.create_index('ix_agent_nodes_role', 'agent_nodes', ['role'])
    op.create_index('ix_agent_nodes_status', 'agent_nodes', ['status'])

    # 3. Fleet Assignments
    op.create_table(
        'fleet_assignments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agent_nodes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('assignment_type', sa.String(length=64), server_default='primary'),
        sa.Column('status', sa.String(length=32), server_default='active'),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index('ix_fleet_assignments_project_id', 'fleet_assignments', ['project_id'])
    op.create_index('ix_fleet_assignments_agent_id', 'fleet_assignments', ['agent_id'])

    # 4. Project Execution Plans
    op.create_table(
        'project_execution_plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('orchestration_mode', sa.String(length=32), server_default='standard'),
        sa.Column('required_roles', postgresql.JSONB(astext_type=sa.Text()), server_default='[]'),
        sa.Column('estimated_cost', sa.Float(), server_default='0.0'),
        sa.Column('priority_override', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=32), server_default='draft'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )
    op.create_index('ix_project_execution_plans_project_id', 'project_execution_plans', ['project_id'])

    # 5. Project Agent Allocations
    op.create_table(
        'project_agent_allocations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(length=32), nullable=False),
        sa.Column('count', sa.Integer(), server_default='1'),
        sa.Column('allocated_count', sa.Integer(), server_default='0'),
        sa.Column('is_satisfied', sa.Boolean(), server_default='false')
    )
    op.create_index('ix_project_agent_allocations_project_id', 'project_agent_allocations', ['project_id'])

def downgrade():
    op.drop_table('project_agent_allocations')
    op.drop_table('project_execution_plans')
    op.drop_table('fleet_assignments')
    op.drop_table('agent_nodes')
    op.drop_table('fleet_clusters')
