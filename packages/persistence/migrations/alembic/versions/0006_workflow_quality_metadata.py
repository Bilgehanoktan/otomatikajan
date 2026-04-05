"""add workflow quality and subtask review metadata

Revision ID: 0006_workflow_quality_metadata
Revises: cce4d9bf9404
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0006_workflow_quality_metadata"
down_revision = "0005_fix_schema_hardening"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Projects table columns
    p_cols = [c['name'] for c in inspector.get_columns("projects")]
    if "workflow_template" not in p_cols:
        op.add_column("projects", sa.Column("workflow_template", sa.String(length=32), nullable=False, server_default="default"))
        op.create_index("ix_projects_workflow_template", "projects", ["workflow_template"], unique=False)
    if "quality_profile" not in p_cols:
        op.add_column("projects", sa.Column("quality_profile", sa.String(length=32), nullable=False, server_default="standard"))
        op.create_index("ix_projects_quality_profile", "projects", ["quality_profile"], unique=False)
    if "acceptance_criteria" not in p_cols:
        op.add_column("projects", sa.Column("acceptance_criteria", postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default=sa.text("'[]'::jsonb")))
    if "execution_context" not in p_cols:
        op.add_column("projects", sa.Column("execution_context", postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default=sa.text("'{}'::jsonb")))
    if "review_required" not in p_cols:
        op.add_column("projects", sa.Column("review_required", sa.Boolean(), nullable=False, server_default=sa.text("false")))

    # Subtasks table columns
    s_cols = [c['name'] for c in inspector.get_columns("subtasks")]
    if "quality_score" not in s_cols:
        op.add_column("subtasks", sa.Column("quality_score", sa.Float(), nullable=True))
    if "quality_detail" not in s_cols:
        op.add_column("subtasks", sa.Column("quality_detail", postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default=sa.text("'{}'::jsonb")))
    if "reviewed" not in s_cols:
        op.add_column("subtasks", sa.Column("reviewed", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    if "review_notes" not in s_cols:
        op.add_column("subtasks", sa.Column("review_notes", postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default=sa.text("'[]'::jsonb")))

    op.alter_column("projects", "workflow_template", server_default=None)
    op.alter_column("projects", "quality_profile", server_default=None)
    op.alter_column("projects", "acceptance_criteria", server_default=None)
    op.alter_column("projects", "execution_context", server_default=None)
    op.alter_column("projects", "review_required", server_default=None)
    op.alter_column("subtasks", "quality_detail", server_default=None)
    op.alter_column("subtasks", "reviewed", server_default=None)
    op.alter_column("subtasks", "review_notes", server_default=None)


def downgrade():
    op.drop_column("subtasks", "review_notes")
    op.drop_column("subtasks", "reviewed")
    op.drop_column("subtasks", "quality_detail")
    op.drop_column("subtasks", "quality_score")

    op.drop_index("ix_projects_quality_profile", table_name="projects")
    op.drop_index("ix_projects_workflow_template", table_name="projects")

    op.drop_column("projects", "review_required")
    op.drop_column("projects", "execution_context")
    op.drop_column("projects", "acceptance_criteria")
    op.drop_column("projects", "quality_profile")
    op.drop_column("projects", "workflow_template")
