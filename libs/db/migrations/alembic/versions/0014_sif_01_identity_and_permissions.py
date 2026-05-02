"""SIF-01 Identity and Permissions

Revision ID: 0014_sif01_identity
Revises: 0013_evolution_tables
Create Date: 2026-04-23 08:50:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision: str = '0014_sif01_identity'
down_revision: Union[str, None] = '0013_evolution_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create operators table
    op.create_table('operators',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), server_default='AUDIT_OBSERVER', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('department', sa.String(length=100), nullable=True),
        sa.Column('region', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username'),
        if_not_exists=True
    )
    op.create_index(op.f('ix_operators_email'), 'operators', ['email'], unique=True)

    # 2. Create system_identities table
    op.create_table('system_identities',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('identity_type', sa.String(length=50), nullable=False),
        sa.Column('role', sa.String(length=50), server_default='AUTONOMOUS_AGENT', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('api_key_hash', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        if_not_exists=True
    )

    # 3. Create permission_grants table
    op.create_table('permission_grants',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('operator_id', sa.UUID(), nullable=True),
        sa.Column('system_id', sa.UUID(), nullable=True),
        sa.Column('permission', sa.String(length=100), nullable=False),
        sa.Column('scope_type', sa.String(length=50), server_default='global', nullable=False),
        sa.Column('scope_value', sa.String(length=255), nullable=True),
        sa.Column('effect', sa.String(length=10), server_default='allow', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('granted_by', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['operator_id'], ['operators.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['system_id'], ['system_identities.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True
    )
    op.create_index(op.f('ix_permission_grants_permission'), 'permission_grants', ['permission'], unique=False)

    # 4. Data Migration: users -> operators
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'users' in inspector.get_table_names():
        op.execute("""
            INSERT INTO operators (id, email, username, hashed_password, role, is_active, created_at)
            SELECT id, email, email, hashed_password, 
                   CASE WHEN is_admin THEN 'SOVEREIGN_PRIME' ELSE 'AUDIT_OBSERVER' END,
                   is_active, created_at
            FROM users
            ON CONFLICT (email) DO NOTHING
        """)


def downgrade() -> None:
    op.drop_table('permission_grants')
    op.drop_table('system_identities')
    op.drop_table('operators')
