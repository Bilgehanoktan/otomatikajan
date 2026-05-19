"""add outcome column to decision lineage

Revision ID: 0015_outcome_lineage
Revises: 0014_sif01_identity
Create Date: 2026-04-26 12:45:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0015_outcome_lineage"
down_revision: str | None = "0014_sif01_identity"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


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
