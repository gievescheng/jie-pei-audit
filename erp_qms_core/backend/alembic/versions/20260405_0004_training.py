"""add training_employees and training_records tables

Revision ID: 20260405_0004
Revises: 20260405_0003
Create Date: 2026-04-05 02:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260405_0004"
down_revision = "20260405_0003"
branch_labels = None
depends_on = None


def audit_columns():
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.Text(), nullable=False, server_default="system"),
        sa.Column("updated_by", sa.Text(), nullable=False, server_default="system"),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    ]


def upgrade() -> None:
    op.create_table(
        "training_employees",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("emp_no", sa.Text(), nullable=False),
        sa.Column("emp_name", sa.Text(), nullable=False),
        sa.Column("department", sa.Text(), nullable=False, server_default=""),
        sa.Column("role", sa.Text(), nullable=False, server_default=""),
        sa.Column("hire_date", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        *audit_columns(),
    )
    op.create_index(
        "ix_training_employees_emp_no",
        "training_employees",
        ["emp_no"],
        unique=True,
    )

    op.create_table(
        "training_records",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column(
            "employee_id",
            sa.Text(),
            sa.ForeignKey("training_employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("course_name", sa.Text(), nullable=False),
        sa.Column("training_date", sa.Text(), nullable=False, server_default=""),
        sa.Column("training_type", sa.Text(), nullable=False, server_default="內訓"),
        sa.Column("result", sa.Text(), nullable=False, server_default="合格"),
        sa.Column("certificate_no", sa.Text(), nullable=False, server_default="無"),
        sa.Column("validity_months", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("remarks", sa.Text(), nullable=False, server_default=""),
        *audit_columns(),
    )
    op.create_index(
        "ix_training_records_employee_id",
        "training_records",
        ["employee_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_training_records_employee_id", table_name="training_records")
    op.drop_table("training_records")
    op.drop_index("ix_training_employees_emp_no", table_name="training_employees")
    op.drop_table("training_employees")
