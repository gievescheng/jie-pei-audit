"""add calibration_instruments and calibration_records tables

Revision ID: 20260405_0002
Revises: 20260317_0001
Create Date: 2026-04-05 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260405_0002"
down_revision = "20260328_0002"
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
        "calibration_instruments",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("instrument_code", sa.Text(), nullable=False),
        sa.Column("instrument_name", sa.Text(), nullable=False),
        sa.Column("instrument_type", sa.Text(), nullable=False, server_default=""),
        sa.Column("model_no", sa.Text(), nullable=False, server_default=""),
        sa.Column("serial_no", sa.Text(), nullable=False, server_default=""),
        sa.Column("location", sa.Text(), nullable=False, server_default=""),
        sa.Column("keeper", sa.Text(), nullable=False, server_default=""),
        sa.Column("brand", sa.Text(), nullable=False, server_default=""),
        sa.Column("calib_method", sa.Text(), nullable=False, server_default=""),
        sa.Column("interval_days", sa.Integer(), nullable=False, server_default="365"),
        sa.Column("needs_msa", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        *audit_columns(),
    )
    op.create_index(
        "ix_calibration_instruments_code",
        "calibration_instruments",
        ["instrument_code"],
        unique=True,
    )

    op.create_table(
        "calibration_records",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column(
            "instrument_id",
            sa.Text(),
            sa.ForeignKey("calibration_instruments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("calibration_date", sa.Text(), nullable=False),
        sa.Column("next_due_date", sa.Text(), nullable=True),
        sa.Column("result", sa.Text(), nullable=False, server_default="合格"),
        sa.Column("calibrated_by", sa.Text(), nullable=False, server_default=""),
        sa.Column("certificate_no", sa.Text(), nullable=False, server_default=""),
        sa.Column("remarks", sa.Text(), nullable=False, server_default=""),
        *audit_columns(),
    )
    op.create_index(
        "ix_calibration_records_instrument_id",
        "calibration_records",
        ["instrument_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_calibration_records_instrument_id", table_name="calibration_records")
    op.drop_table("calibration_records")
    op.drop_index("ix_calibration_instruments_code", table_name="calibration_instruments")
    op.drop_table("calibration_instruments")
