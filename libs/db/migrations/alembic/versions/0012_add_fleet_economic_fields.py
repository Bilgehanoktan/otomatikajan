"""add fleet economic fields

Revision ID: 0012_add_fleet_economic_fields
Revises: 0011_add_isolation_and_autonomy_fields
Create Date: 2026-04-16 03:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0012_add_fleet_economic_fields'
down_revision: Union[str, None] = '0011_add_isolation_and_autonomy_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add budget and burn rate columns
    op.add_column('projects', sa.Column('current_budget_usd', sa.Float(), server_default='0.0', nullable=False))
    op.add_column('projects', sa.Column('hourly_burn_rate', sa.Float(), server_default='0.0', nullable=False))
    
    # Add economic_profile JSONB
    op.add_column('projects', sa.Column('economic_profile', postgresql.JSONB(astext_type=sa.Text()), 
        server_default='{"steering_policy": "cost_optimized", "min_budget_threshold": 10.0, "auto_scale_concurrency": true}', 
        nullable=False))


def downgrade() -> None:
    op.drop_column('projects', 'economic_profile')
    op.drop_column('projects', 'hourly_burn_rate')
    op.drop_column('projects', 'current_budget_usd')
