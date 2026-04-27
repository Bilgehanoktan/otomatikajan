"""add_governance_proof_fabric

Revision ID: e4a7b5d12345
Revises: 4bd5655fe01b
Create Date: 2026-04-27 01:25:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import libs.db.base

revision: str = 'e4a7b5d12345'
down_revision: Union[str, None] = '4bd5655fe01b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Enums ---
    # Note: ProofEventType and ProofSealStatus are new.
    # GovernorDomain is reused.
    # ProofEventType and ProofSealStatus will be treated as Strings to avoid native ENUM issues
    pass

    # --- Tables ---
    op.create_table('governance_proof_events',
        sa.Column('id', libs.db.base.GUID(), nullable=False),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('domain', postgresql.ENUM('WORKFLOW', 'INCIDENT', 'APPROVAL', 'POLICY', 'REPAIR', 'META', name='governordomain', create_type=False), nullable=True),
        sa.Column('entity_id', sa.String(length=100), nullable=True),
        sa.Column('payload_hash', sa.String(length=64), nullable=False),
        sa.Column('payload_canonical', sa.Text(), nullable=False),
        sa.Column('prev_event_hash', sa.String(length=64), nullable=True),
        sa.Column('event_hash', sa.String(length=64), nullable=False),
        sa.Column('chain_index', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_governance_proof_events_chain_index'), 'governance_proof_events', ['chain_index'], unique=False)
    op.create_index(op.f('ix_governance_proof_events_created_at'), 'governance_proof_events', ['created_at'], unique=False)
    op.create_index(op.f('ix_governance_proof_events_domain'), 'governance_proof_events', ['domain'], unique=False)
    op.create_index(op.f('ix_governance_proof_events_entity_id'), 'governance_proof_events', ['entity_id'], unique=False)
    op.create_index(op.f('ix_governance_proof_events_event_hash'), 'governance_proof_events', ['event_hash'], unique=False)
    op.create_index(op.f('ix_governance_proof_events_event_type'), 'governance_proof_events', ['event_type'], unique=False)

    op.create_table('governance_proof_snapshots',
        sa.Column('id', libs.db.base.GUID(), nullable=False),
        sa.Column('snapshot_name', sa.String(length=200), nullable=False),
        sa.Column('start_chain_index', sa.BigInteger(), nullable=False),
        sa.Column('end_chain_index', sa.BigInteger(), nullable=False),
        sa.Column('event_count', sa.Integer(), nullable=True),
        sa.Column('merkle_root', sa.String(length=64), nullable=False),
        sa.Column('snapshot_hash', sa.String(length=64), nullable=False),
        sa.Column('seal_status', sa.String(length=32), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('sealed_by', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_governance_proof_snapshots_created_at'), 'governance_proof_snapshots', ['created_at'], unique=False)
    op.create_index(op.f('ix_governance_proof_snapshots_seal_status'), 'governance_proof_snapshots', ['seal_status'], unique=False)

    op.create_table('governance_merkle_nodes',
        sa.Column('id', libs.db.base.GUID(), nullable=False),
        sa.Column('snapshot_id', libs.db.base.GUID(), nullable=False),
        sa.Column('node_level', sa.Integer(), nullable=False),
        sa.Column('node_index', sa.Integer(), nullable=False),
        sa.Column('left_hash', sa.String(length=64), nullable=True),
        sa.Column('right_hash', sa.String(length=64), nullable=True),
        sa.Column('node_hash', sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_governance_merkle_nodes_snapshot_id'), 'governance_merkle_nodes', ['snapshot_id'], unique=False)

    op.create_table('governance_proof_verifications',
        sa.Column('id', libs.db.base.GUID(), nullable=False),
        sa.Column('target_type', sa.String(length=50), nullable=False),
        sa.Column('target_id', sa.String(length=100), nullable=False),
        sa.Column('snapshot_id', libs.db.base.GUID(), nullable=True),
        sa.Column('verification_status', sa.String(length=32), nullable=False),
        sa.Column('proof_payload', postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('verified_by', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_governance_proof_verifications_snapshot_id'), 'governance_proof_verifications', ['snapshot_id'], unique=False)
    op.create_index(op.f('ix_governance_proof_verifications_target_id'), 'governance_proof_verifications', ['target_id'], unique=False)
    op.create_index(op.f('ix_governance_proof_verifications_verified_at'), 'governance_proof_verifications', ['verified_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_governance_proof_verifications_verified_at'), table_name='governance_proof_verifications')
    op.drop_index(op.f('ix_governance_proof_verifications_target_id'), table_name='governance_proof_verifications')
    op.drop_index(op.f('ix_governance_proof_verifications_snapshot_id'), table_name='governance_proof_verifications')
    op.drop_table('governance_proof_verifications')
    op.drop_index(op.f('ix_governance_merkle_nodes_snapshot_id'), table_name='governance_merkle_nodes')
    op.drop_table('governance_merkle_nodes')
    op.drop_index(op.f('ix_governance_proof_snapshots_seal_status'), table_name='governance_proof_snapshots')
    op.drop_index(op.f('ix_governance_proof_snapshots_created_at'), table_name='governance_proof_snapshots')
    op.drop_table('governance_proof_snapshots')
    op.drop_index(op.f('ix_governance_proof_events_event_type'), table_name='governance_proof_events')
    op.drop_index(op.f('ix_governance_proof_events_event_hash'), table_name='governance_proof_events')
    op.drop_index(op.f('ix_governance_proof_events_entity_id'), table_name='governance_proof_events')
    op.drop_index(op.f('ix_governance_proof_events_domain'), table_name='governance_proof_events')
    op.drop_index(op.f('ix_governance_proof_events_created_at'), table_name='governance_proof_events')
    op.drop_index(op.f('ix_governance_proof_events_chain_index'), table_name='governance_proof_events')
    op.drop_table('governance_proof_events')
    
    # op.execute("DROP TYPE proofsealstatus")
    # op.execute("DROP TYPE proofeventtype")
    pass
