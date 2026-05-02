"""execution_safety_layer

Revision ID: 7ce444aee8f5
Revises: 0015b_gov_base
Create Date: 2026-04-27 00:24:32.552001
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '7ce444aee8f5'
down_revision: Union[str, None] = '0015b_gov_base'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # governor_actions
    op.add_column('governor_actions', sa.Column('justification', sa.Text(), nullable=True))
    op.add_column('governor_actions', sa.Column('operator_role', sa.String(length=64), nullable=True))
    op.add_column('governor_actions', sa.Column('override_flag', sa.Integer(), server_default='0', nullable=True))
    op.add_column('governor_actions', sa.Column('guardrail_bypassed', sa.Integer(), server_default='0', nullable=True))
    op.add_column('governor_actions', sa.Column('approval_snapshot', sa.JSON(), nullable=True))

    # governor_escalations
    op.add_column('governor_escalations', sa.Column('resolution_type', sa.String(length=64), nullable=True))
    op.add_column('governor_escalations', sa.Column('resolution_notes', sa.Text(), nullable=True))
    op.add_column('governor_escalations', sa.Column('resolved_by', sa.String(length=64), nullable=True))
    op.add_column('governor_escalations', sa.Column('final_action', sa.String(length=64), nullable=True))

def downgrade() -> None:
    # governor_actions
    op.drop_column('governor_actions', 'justification')
    op.drop_column('governor_actions', 'operator_role')
    op.drop_column('governor_actions', 'override_flag')
    op.drop_column('governor_actions', 'guardrail_bypassed')
    op.drop_column('governor_actions', 'approval_snapshot')

    # governor_escalations
    op.drop_column('governor_escalations', 'resolution_type')
    op.drop_column('governor_escalations', 'resolution_notes')
    op.drop_column('governor_escalations', 'resolved_by')
    op.drop_column('governor_escalations', 'final_action')
