"""add outcome column to decision lineage

Revision ID: 0015_add_outcome_to_decision_lineage
Revises: 0014_sif_01_identity_and_permissions
Create Date: 2026-04-26 12:45:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0015_add_outcome_to_decision_lineage"
down_revision: Union[str, None] = "0014_sif_01_identity_and_permissions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("decision_lineage")}

    if "outcome" not in columns:
        op.add_column(
            "decision_lineage",
            sa.Column("outcome", sa.String(), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("decision_lineage")}

    if "outcome" in columns:
        op.drop_column("decision_lineage", "outcome")
