"""add isolation and autonomy fields

Revision ID: 0011_add_isolation_and_autonomy_fields
Revises: 0010_add_operational_governance_tables
Create Date: 2026-04-16 03:35:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0011_add_isolation_and_autonomy_fields'
down_revision: Union[str, None] = '0010_add_operational_governance_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Add isolation_tier
    op.add_column('projects', sa.Column('isolation_tier', sa.Integer(), server_default='2', nullable=False))
    op.create_index(op.f('ix_projects_isolation_tier'), 'projects', ['isolation_tier'], unique=False)
    
    # Add autonomy_envelope
    op.add_column('projects', sa.Column('autonomy_envelope', postgresql.JSONB(astext_type=sa.Text()), server_default='{"mode": "advisory", "allow_auto_patch": false, "max_risk_score": 0.3, "isolation_zone": "global"}', nullable=False))
    
    # Add concurrency_limit
    op.add_column('projects', sa.Column('concurrency_limit', sa.Integer(), server_default='5', nullable=False))

def downgrade() -> None:
    op.drop_column('projects', 'concurrency_limit')
    op.drop_column('projects', 'autonomy_envelope')
    op.drop_index(op.f('ix_projects_isolation_tier'), table_name='projects')
    op.drop_column('projects', 'isolation_tier')
