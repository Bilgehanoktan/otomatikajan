"""add_review_ledger_entries

Revision ID: f28a0b1c2d3e
Revises: e1a49df5d6bb
Create Date: 2026-06-08 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "f28a0b1c2d3e"
down_revision: Union[str, None] = "e1a49df5d6bb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


json_type = postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite")


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if "bilgeapi_review_ledger_entries" not in tables:
        op.create_table(
            "bilgeapi_review_ledger_entries",
            sa.Column("id", sa.String(length=64), nullable=False),
            sa.Column("chain_id", sa.String(length=128), nullable=False),
            sa.Column("sequence_no", sa.Integer(), nullable=False),
            sa.Column("event_type", sa.String(length=64), nullable=False),
            sa.Column("entity_type", sa.String(length=64), nullable=False),
            sa.Column("entity_id", sa.String(length=64), nullable=False),
            sa.Column("actor_id", sa.String(length=64), nullable=True),
            sa.Column("previous_hash", sa.String(length=64), nullable=True),
            sa.Column("payload_hash", sa.String(length=64), nullable=False),
            sa.Column("event_hash", sa.String(length=64), nullable=False),
            sa.Column("payload_summary", json_type, nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("chain_id", "sequence_no", name="uq_review_ledger_chain_sequence"),
        )
        op.create_index(op.f("ix_bilgeapi_review_ledger_entries_actor_id"), "bilgeapi_review_ledger_entries", ["actor_id"], unique=False)
        op.create_index(op.f("ix_bilgeapi_review_ledger_entries_chain_id"), "bilgeapi_review_ledger_entries", ["chain_id"], unique=False)
        op.create_index(op.f("ix_bilgeapi_review_ledger_entries_created_at"), "bilgeapi_review_ledger_entries", ["created_at"], unique=False)
        op.create_index(op.f("ix_bilgeapi_review_ledger_entries_entity_id"), "bilgeapi_review_ledger_entries", ["entity_id"], unique=False)
        op.create_index(op.f("ix_bilgeapi_review_ledger_entries_entity_type"), "bilgeapi_review_ledger_entries", ["entity_type"], unique=False)
        op.create_index(op.f("ix_bilgeapi_review_ledger_entries_event_hash"), "bilgeapi_review_ledger_entries", ["event_hash"], unique=True)
        op.create_index(op.f("ix_bilgeapi_review_ledger_entries_event_type"), "bilgeapi_review_ledger_entries", ["event_type"], unique=False)


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if "bilgeapi_review_ledger_entries" in tables:
        op.drop_index(op.f("ix_bilgeapi_review_ledger_entries_event_type"), table_name="bilgeapi_review_ledger_entries")
        op.drop_index(op.f("ix_bilgeapi_review_ledger_entries_event_hash"), table_name="bilgeapi_review_ledger_entries")
        op.drop_index(op.f("ix_bilgeapi_review_ledger_entries_entity_type"), table_name="bilgeapi_review_ledger_entries")
        op.drop_index(op.f("ix_bilgeapi_review_ledger_entries_entity_id"), table_name="bilgeapi_review_ledger_entries")
        op.drop_index(op.f("ix_bilgeapi_review_ledger_entries_created_at"), table_name="bilgeapi_review_ledger_entries")
        op.drop_index(op.f("ix_bilgeapi_review_ledger_entries_chain_id"), table_name="bilgeapi_review_ledger_entries")
        op.drop_index(op.f("ix_bilgeapi_review_ledger_entries_actor_id"), table_name="bilgeapi_review_ledger_entries")
        op.drop_table("bilgeapi_review_ledger_entries")
