"""comprehensive core resync

Revision ID: 0017_core_resync
Revises: 0016
Create Date: 2026-05-02 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0017_core_resync'
down_revision = '0016'
branch_labels = None
depends_on = None

def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # --- projects table ---
    proj_cols = [c['name'] for c in inspector.get_columns('projects')]
    
    if 'metadata_' not in proj_cols:
        op.add_column('projects', sa.Column('metadata_', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False))
    
    if 'acceptance_criteria' not in proj_cols:
        op.add_column('projects', sa.Column('acceptance_criteria', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False))
        
    if 'execution_context' not in proj_cols:
        op.add_column('projects', sa.Column('execution_context', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False))
        
    if 'checkpoint_data' not in proj_cols:
        op.add_column('projects', sa.Column('checkpoint_data', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False))
        
    if 'review_required' not in proj_cols:
        op.add_column('projects', sa.Column('review_required', sa.Boolean(), server_default='false', nullable=False))
        
    if 'workflow_template' not in proj_cols:
        op.add_column('projects', sa.Column('workflow_template', sa.String(32), server_default='default', nullable=False))
        op.create_index(op.f('ix_projects_workflow_template'), 'projects', ['workflow_template'], unique=False)
        
    if 'quality_profile' not in proj_cols:
        op.add_column('projects', sa.Column('quality_profile', sa.String(32), server_default='standard', nullable=False))
        op.create_index(op.f('ix_projects_quality_profile'), 'projects', ['quality_profile'], unique=False)

    # --- subtasks table ---
    sub_cols = [c['name'] for c in inspector.get_columns('subtasks')]
    
    if 'metadata_' not in sub_cols:
        op.add_column('subtasks', sa.Column('metadata_', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False))
        
    if 'tags' not in sub_cols:
        op.add_column('subtasks', sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False))
        
    if 'input_data' not in sub_cols:
        op.add_column('subtasks', sa.Column('input_data', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False))
        
    if 'input_schema' not in sub_cols:
        op.add_column('subtasks', sa.Column('input_schema', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False))
        
    if 'quality_detail' not in sub_cols:
        op.add_column('subtasks', sa.Column('quality_detail', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False))

    if 'latency_s' not in sub_cols:
        op.add_column('subtasks', sa.Column('latency_s', sa.Float(), server_default='0.0', nullable=False))

    if 'action' not in sub_cols:
        op.add_column('subtasks', sa.Column('action', sa.String(128), server_default='run_agent', nullable=False))
        
    if 'dependencies' not in sub_cols:
        op.add_column('subtasks', sa.Column('dependencies', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False))

def downgrade():
    # Typically we don't drop columns in a resync unless absolutely necessary
    pass
