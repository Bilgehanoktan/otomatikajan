"""update system_identities fields

Revision ID: 0018_update_system_identity
Revises: 0017_core_resync
Create Date: 2026-05-05 04:00:00.000000
"""
import sqlalchemy as sa
from alembic import op

revision = '0018_update_system_identity'
down_revision = '0017_core_resync'
branch_labels = None
depends_on = None

def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = [c['name'] for c in inspector.get_columns('system_identities')]

    if 'last_used_at' not in cols:
        op.add_column('system_identities', sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True))
    if 'key_expires_at' not in cols:
        op.add_column('system_identities', sa.Column('key_expires_at', sa.DateTime(timezone=True), nullable=True))
    if 'trust_score' not in cols:
        op.add_column('system_identities', sa.Column('trust_score', sa.Integer(), server_default='100', nullable=False))
    if 'risk_level' not in cols:
        op.add_column('system_identities', sa.Column('risk_level', sa.String(20), server_default='LOW', nullable=False))
    if 'quarantined_at' not in cols:
        op.add_column('system_identities', sa.Column('quarantined_at', sa.DateTime(timezone=True), nullable=True))
    if 'risk_reason' not in cols:
        op.add_column('system_identities', sa.Column('risk_reason', sa.String(255), nullable=True))

def downgrade():
    op.drop_column('system_identities', 'risk_reason')
    op.drop_column('system_identities', 'quarantined_at')
    op.drop_column('system_identities', 'risk_level')
    op.drop_column('system_identities', 'trust_score')
    op.drop_column('system_identities', 'key_expires_at')
    op.drop_column('system_identities', 'last_used_at')
