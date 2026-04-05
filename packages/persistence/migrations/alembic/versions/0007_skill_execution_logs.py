"""skill_execution_logs table

Revision ID: 0007_skill_execution_logs
Revises: 0006_workflow_quality_metadata
Create Date: 2026-03-29 02:55:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0007_skill_execution_logs'
down_revision = '0006_workflow_quality_metadata'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'skill_execution_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('agent_id', sa.String(length=64), nullable=True),
        sa.Column('skill_id', sa.String(length=64), nullable=False),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('data', postgresql.JSONB(), nullable=True),
        sa.Column('duration_s', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE')
    )
    op.create_index('ix_skill_execution_logs_project_id', 'skill_execution_logs', ['project_id'], unique=False)
    op.create_index('ix_skill_execution_logs_agent_id', 'skill_execution_logs', ['agent_id'], unique=False)
    op.create_index('ix_skill_execution_logs_skill_id', 'skill_execution_logs', ['skill_id'], unique=False)
    op.create_index('ix_skill_execution_logs_created_at', 'skill_execution_logs', ['created_at'], unique=False)

def downgrade():
    op.drop_index('ix_skill_execution_logs_created_at', table_name='skill_execution_logs')
    op.drop_index('ix_skill_execution_logs_skill_id', table_name='skill_execution_logs')
    op.drop_index('ix_skill_execution_logs_agent_id', table_name='skill_execution_logs')
    op.drop_index('ix_skill_execution_logs_project_id', table_name='skill_execution_logs')
    op.drop_table('skill_execution_logs')
