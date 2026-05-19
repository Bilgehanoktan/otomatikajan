"""Standardize status names (done->completed, failed->error)

Revision ID: 0003_standardize_status_names
Revises: 0002_repair_tables
Create Date: 2026-03-21 20:00:00.000000

Bu migration, 'projects' ve 'subtasks' tablolarındaki 'done' ve 'failed' 
değerlerini yeni canonical isimler olan 'completed' ve 'error' ile günceller.
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "0003_standardize_status_names"
down_revision = "0002_repair_tables"
branch_labels = None
depends_on = None

def upgrade() -> None:
    # ── projects tablosu ─────────────────────────────────
    op.execute(
        "UPDATE projects SET status = 'completed' WHERE status = 'done'"
    )
    op.execute(
        "UPDATE projects SET status = 'error' WHERE status = 'failed'"
    )

    # ── subtasks tablosu ─────────────────────────────────
    op.execute(
        "UPDATE subtasks SET status = 'completed' WHERE status = 'done'"
    )
    op.execute(
        "UPDATE subtasks SET status = 'error' WHERE status = 'failed'"
    )

def downgrade() -> None:
    # Gerekirse geri al (tersine çevir)
    op.execute(
        "UPDATE projects SET status = 'done' WHERE status = 'completed'"
    )
    op.execute(
        "UPDATE projects SET status = 'failed' WHERE status = 'error'"
    )
    op.execute(
        "UPDATE subtasks SET status = 'done' WHERE status = 'completed'"
    )
    op.execute(
        "UPDATE subtasks SET status = 'failed' WHERE status = 'error'"
    )
