"""standardize_status_and_project_id_sync

Revision ID: af7ebd1309a2
Revises: 0008_add_meta_to_repair_jobs
Create Date: 2026-03-29 21:29:54.271867
"""
from collections.abc import Sequence

from alembic import op

revision: str = 'af7ebd1309a2'
down_revision: str | None = '0008_add_meta_to_repair_jobs'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Update existing legacy statuses if any exist as plain strings or old enum values
    # op.execute is safer for direct data manipulation in migration
    op.execute("UPDATE projects SET status = 'COMPLETED' WHERE status IN ('done', 'SUCCESS', 'completed')")
    op.execute("UPDATE projects SET status = 'ERROR' WHERE status IN ('failed', 'FAILED', 'error')")
    op.execute("UPDATE subtasks SET status = 'COMPLETED' WHERE status IN ('done', 'SUCCESS', 'completed')")
    op.execute("UPDATE subtasks SET status = 'ERROR' WHERE status IN ('failed', 'FAILED', 'error')")

def downgrade() -> None:
    # No easy way to revert status normalization without risk of data loss
    pass
