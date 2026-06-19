"""add_ai_patch_suggestions

Revision ID: a29c4f83b2d1
Revises: f28a0b1c2d3e
Create Date: 2026-06-09
"""
from alembic import op
import sqlalchemy as sa


revision = "a29c4f83b2d1"
down_revision = "f28a0b1c2d3e"
branch_labels = None
depends_on = None


json_type = sa.JSON().with_variant(sa.JSON(), "sqlite")


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if table_name not in inspector.get_table_names():
        return False
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def upgrade() -> None:
    if not _has_table("bilgeapi_ai_patch_suggestions"):
        op.create_table(
            "bilgeapi_ai_patch_suggestions",
            sa.Column("id", sa.String(length=64), primary_key=True),
            sa.Column("pr_draft_id", sa.String(length=64), sa.ForeignKey("bilgeapi_pr_drafts.id"), nullable=False),
            sa.Column("feedback_id", sa.String(length=64), sa.ForeignKey("bilgeapi_pr_review_feedbacks.id"), nullable=True),
            sa.Column("revision_id", sa.String(length=64), sa.ForeignKey("bilgeapi_patch_revisions.id"), nullable=True),
            sa.Column("provider", sa.String(length=32), nullable=False, server_default="mock"),
            sa.Column("model_name", sa.String(length=128), nullable=True),
            sa.Column("prompt_hash", sa.String(length=128), nullable=False),
            sa.Column("context_summary", json_type, nullable=True),
            sa.Column("suggested_patch_code", sa.Text(), nullable=False),
            sa.Column("rationale", sa.Text(), nullable=True),
            sa.Column("risk_notes", sa.Text(), nullable=True),
            sa.Column("risk_level", sa.String(length=32), nullable=False, server_default="LOW"),
            sa.Column("verification_id", sa.String(length=64), sa.ForeignKey("bilgeapi_pr_verifications.id"), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="GENERATED"),
            sa.Column("created_by", sa.String(length=64), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_bilgeapi_ai_patch_suggestions_pr_draft_id", "bilgeapi_ai_patch_suggestions", ["pr_draft_id"])
        op.create_index("ix_bilgeapi_ai_patch_suggestions_feedback_id", "bilgeapi_ai_patch_suggestions", ["feedback_id"])
        op.create_index("ix_bilgeapi_ai_patch_suggestions_revision_id", "bilgeapi_ai_patch_suggestions", ["revision_id"])
        op.create_index("ix_bilgeapi_ai_patch_suggestions_prompt_hash", "bilgeapi_ai_patch_suggestions", ["prompt_hash"])
        op.create_index("ix_bilgeapi_ai_patch_suggestions_risk_level", "bilgeapi_ai_patch_suggestions", ["risk_level"])
        op.create_index("ix_bilgeapi_ai_patch_suggestions_verification_id", "bilgeapi_ai_patch_suggestions", ["verification_id"])
        op.create_index("ix_bilgeapi_ai_patch_suggestions_status", "bilgeapi_ai_patch_suggestions", ["status"])
        op.create_index("ix_bilgeapi_ai_patch_suggestions_created_at", "bilgeapi_ai_patch_suggestions", ["created_at"])

    if not _has_column("bilgeapi_pr_verifications", "ai_suggestion_id"):
        with op.batch_alter_table("bilgeapi_pr_verifications") as batch_op:
            batch_op.add_column(sa.Column("ai_suggestion_id", sa.String(length=64), nullable=True))
            batch_op.create_index("ix_bilgeapi_pr_verifications_ai_suggestion_id", ["ai_suggestion_id"])
            batch_op.create_foreign_key(
                "fk_pr_verifications_ai_suggestion_id",
                "bilgeapi_ai_patch_suggestions",
                ["ai_suggestion_id"],
                ["id"],
            )


def downgrade() -> None:
    if _has_column("bilgeapi_pr_verifications", "ai_suggestion_id"):
        with op.batch_alter_table("bilgeapi_pr_verifications") as batch_op:
            batch_op.drop_constraint("fk_pr_verifications_ai_suggestion_id", type_="foreignkey")
            batch_op.drop_index("ix_bilgeapi_pr_verifications_ai_suggestion_id")
            batch_op.drop_column("ai_suggestion_id")

    if _has_table("bilgeapi_ai_patch_suggestions"):
        op.drop_table("bilgeapi_ai_patch_suggestions")
