"""Adopt schema fields already deployed before formal migration tracking.

Revision ID: 5cf84776dfef
Revises: e1f8a846b9c9
Create Date: 2026-07-09 19:10:32.199422
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "5cf84776dfef"
down_revision: str | None = "e1f8a846b9c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _add_column_if_missing(table_name: str, column: sa.Column) -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if table_name not in inspector.get_table_names():
        return
    existing = {item["name"] for item in inspector.get_columns(table_name)}
    if column.name not in existing:
        op.add_column(table_name, column)


def _create_index_if_missing(
    index_name: str,
    table_name: str,
    columns: list[str],
) -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if table_name not in inspector.get_table_names():
        return
    existing = {item["name"] for item in inspector.get_indexes(table_name)}
    if index_name not in existing:
        op.create_index(index_name, table_name, columns, unique=False)


def upgrade() -> None:
    _add_column_if_missing(
        "agent_nodes", sa.Column("success_count", sa.Integer(), server_default="0")
    )
    _add_column_if_missing(
        "agent_nodes", sa.Column("failure_count", sa.Integer(), server_default="0")
    )
    _add_column_if_missing("ceo_decisions", sa.Column("summary", sa.Text()))
    _add_column_if_missing(
        "ceo_decisions",
        sa.Column("context", postgresql.JSONB().with_variant(sa.JSON(), "sqlite")),
    )
    _add_column_if_missing(
        "ceo_decisions", sa.Column("applied_at", sa.DateTime(timezone=True))
    )
    _add_column_if_missing("decision_lineage", sa.Column("summary", sa.Text()))
    _add_column_if_missing(
        "improvement_opportunities",
        sa.Column(
            "affected_files",
            postgresql.JSONB().with_variant(sa.JSON(), "sqlite"),
        ),
    )
    _add_column_if_missing(
        "improvement_opportunities",
        sa.Column("severity_score", sa.Float(), server_default="0"),
    )
    _add_column_if_missing(
        "improvement_opportunities",
        sa.Column("impact", sa.Float(), server_default="0"),
    )
    _add_column_if_missing(
        "projects", sa.Column("priority_level", sa.Integer(), server_default="50")
    )
    _add_column_if_missing(
        "projects", sa.Column("ceo_managed", sa.Boolean(), server_default=sa.false())
    )
    _add_column_if_missing(
        "sovereign_goals", sa.Column("completed_at", sa.DateTime(timezone=True))
    )
    _create_index_if_missing(
        "ix_projects_ceo_managed", "projects", ["ceo_managed"]
    )


def downgrade() -> None:
    # This revision adopts pre-existing production schema. Removing columns
    # would risk deleting data that may predate this migration record.
    pass
