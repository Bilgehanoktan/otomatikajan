"""add is_pilot to projects

Revision ID: 0009_add_is_pilot_to_projects
Revises: 7cc9f44bc8d0
Create Date: 2026-04-14 21:52:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0009_add_is_pilot_to_projects'
down_revision: Union[str, None] = '7cc9f44bc8d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if column exists first (SRE safety)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = [c['name'] for c in inspector.get_columns("projects")]
    if "is_pilot" not in cols:
        op.add_column('projects', sa.Column('is_pilot', sa.Boolean(), server_default='false', nullable=False))
        op.create_index(op.f('ix_projects_is_pilot'), 'projects', ['is_pilot'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_projects_is_pilot'), table_name='projects')
    op.drop_column('projects', 'is_pilot')
