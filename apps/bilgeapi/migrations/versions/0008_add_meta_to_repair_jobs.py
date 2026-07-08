"""Add meta column to repair_jobs (Faz 12.1 Stabilizasyon)

Revision ID: 0008_add_meta_to_repair_jobs
Revises: 0007_skill_execution_logs
Create Date: 2026-03-29 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0008_add_meta_to_repair_jobs"
down_revision = "f002a05eadd5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # repair_jobs tablosuna meta sütununu ekle
    op.add_column(
        "repair_jobs",
        sa.Column("meta", sa.JSON(), server_default="{}", nullable=True)
    )


def downgrade() -> None:
    op.drop_column("repair_jobs", "meta")
