"""fix project owner fk

Revision ID: 0019_fix_project_owner_fk
Revises: 0018_update_system_identity
Create Date: 2026-05-05 04:10:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '0019_fix_project_owner_fk'
down_revision = '0018_update_system_identity'
branch_labels = None
depends_on = None

def upgrade():
    # 1. Drop existing FK
    op.drop_constraint('projects_owner_id_fkey', 'projects', type_='foreignkey')
    
    # 2. Add new FK to operators
    op.create_foreign_key(
        'projects_owner_id_fkey',
        'projects', 'operators',
        ['owner_id'], ['id'],
        ondelete='SET NULL'
    )

def downgrade():
    op.drop_constraint('projects_owner_id_fkey', 'projects', type_='foreignkey')
    op.create_foreign_key(
        'projects_owner_id_fkey',
        'projects', 'users',
        ['owner_id'], ['id'],
        ondelete='SET NULL'
    )
