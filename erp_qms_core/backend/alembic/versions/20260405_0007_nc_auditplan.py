"""add non_conformances and audit_plans tables

Revision ID: 20260405_0007
Revises: 20260405_0006
Create Date: 2026-04-05 05:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260405_0007"
down_revision = "20260405_0006"
branch_labels = None
depends_on = None

_ts_cols = [
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("created_by", sa.Text(), nullable=False, server_default="system"),
    sa.Column("updated_by", sa.Text(), nullable=False, server_default="system"),
    sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
]


def upgrade() -> None:
    op.create_table(
        "non_conformances",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("nc_no", sa.Text(), nullable=False, unique=True),
        sa.Column("nc_date", sa.Text(), nullable=False, server_default=""),
        sa.Column("dept", sa.Text(), nullable=False, server_default=""),
        sa.Column("nc_type", sa.Text(), nullable=False, server_default=""),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("severity", sa.Text(), nullable=False, server_default=""),
        sa.Column("root_cause", sa.Text(), nullable=False, server_default=""),
        sa.Column("corrective_action", sa.Text(), nullable=False, server_default=""),
        sa.Column("responsible", sa.Text(), nullable=False, server_default=""),
        sa.Column("due_date", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.Text(), nullable=False, server_default=""),
        sa.Column("close_date", sa.Text(), nullable=False, server_default=""),
        sa.Column("effectiveness", sa.Text(), nullable=False, server_default=""),
        *_ts_cols,
    )
    op.create_index("ix_non_conformances_nc_no", "non_conformances", ["nc_no"])

    op.create_table(
        "audit_plans",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("plan_no", sa.Text(), nullable=False, unique=True),
        sa.Column("year", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("period", sa.Text(), nullable=False, server_default=""),
        sa.Column("scheduled_date", sa.Text(), nullable=False, server_default=""),
        sa.Column("dept", sa.Text(), nullable=False, server_default=""),
        sa.Column("scope", sa.Text(), nullable=False, server_default=""),
        sa.Column("auditor", sa.Text(), nullable=False, server_default=""),
        sa.Column("auditee", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.Text(), nullable=False, server_default=""),
        sa.Column("actual_date", sa.Text(), nullable=False, server_default=""),
        sa.Column("findings", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("nc_count", sa.Integer(), nullable=False, server_default="0"),
        *_ts_cols,
    )
    op.create_index("ix_audit_plans_plan_no", "audit_plans", ["plan_no"])


def downgrade() -> None:
    op.drop_index("ix_audit_plans_plan_no", table_name="audit_plans")
    op.drop_table("audit_plans")
    op.drop_index("ix_non_conformances_nc_no", table_name="non_conformances")
    op.drop_table("non_conformances")
