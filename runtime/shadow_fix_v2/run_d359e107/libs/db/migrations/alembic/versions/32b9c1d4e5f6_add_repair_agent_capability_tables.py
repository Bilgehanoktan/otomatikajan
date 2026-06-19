"""add repair agent capability and run tables

Revision ID: 32b9c1d4e5f6
Revises: 007f130e456e
Create Date: 2026-06-11 07:10:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "32b9c1d4e5f6"
down_revision: Union[str, None] = "007f130e456e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

json_type = postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite")


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if not _has_table("repair_agent_capabilities"):
        op.create_table(
            "repair_agent_capabilities",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("agent_key", sa.String(length=64), nullable=False),
            sa.Column("agent_name", sa.String(length=128), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("risk_level", sa.String(length=32), nullable=False, server_default="medium"),
            sa.Column("allowed_directories", json_type, nullable=True),
            sa.Column("blocked_directories", json_type, nullable=True),
            sa.Column("allowed_commands", json_type, nullable=True),
            sa.Column("blocked_commands", json_type, nullable=True),
            sa.Column("sandbox_mode", sa.String(length=32), nullable=False, server_default="read-only"),
            sa.Column("max_cost_limit", sa.Float(), nullable=False, server_default="10.0"),
            sa.Column("requires_human_approval", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("network_policy", sa.String(length=32), nullable=False, server_default="disabled"),
            sa.Column("allowed_domains", json_type, nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("agent_key", name="uq_repair_agent_capabilities_agent_key"),
        )
        op.create_index(
            "ix_repair_agent_capabilities_agent_key",
            "repair_agent_capabilities",
            ["agent_key"],
            unique=False,
        )

    if not _has_table("repair_agent_runs"):
        op.create_table(
            "repair_agent_runs",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("run_id", sa.String(length=64), nullable=False),
            sa.Column("agent_key", sa.String(length=64), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="PENDING"),
            sa.Column("workspace_path", sa.String(length=512), nullable=True),
            sa.Column("input_parameters", json_type, nullable=True),
            sa.Column("commands_executed", json_type, nullable=True),
            sa.Column("policy_violations", json_type, nullable=True),
            sa.Column("exit_code", sa.Integer(), nullable=True),
            sa.Column("stdout", sa.Text(), nullable=True),
            sa.Column("stderr", sa.Text(), nullable=True),
            sa.Column("cost", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("timeout_seconds", sa.Integer(), nullable=False, server_default="300"),
            sa.Column("sandbox_mode", sa.String(length=32), nullable=False),
            sa.Column("network_policy", sa.String(length=32), nullable=False),
            sa.Column("input_hash", sa.String(length=128), nullable=True),
            sa.Column("command_hash", sa.String(length=128), nullable=True),
            sa.Column("output_hash", sa.String(length=128), nullable=True),
            sa.Column("workspace_hash", sa.String(length=128), nullable=True),
            sa.Column("ledger_chain_id", sa.String(length=128), nullable=True),
            sa.Column("created_by", sa.String(length=64), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("run_id", name="uq_repair_agent_runs_run_id"),
        )
        op.create_index("ix_repair_agent_runs_agent_key", "repair_agent_runs", ["agent_key"], unique=False)
        op.create_index("ix_repair_agent_runs_ledger_chain_id", "repair_agent_runs", ["ledger_chain_id"], unique=False)
        op.create_index("ix_repair_agent_runs_run_id", "repair_agent_runs", ["run_id"], unique=False)


def downgrade() -> None:
    if _has_table("repair_agent_runs"):
        op.drop_table("repair_agent_runs")
    if _has_table("repair_agent_capabilities"):
        op.drop_table("repair_agent_capabilities")
