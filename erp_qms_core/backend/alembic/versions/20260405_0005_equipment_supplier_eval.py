"""add equipment_master, maintenance_records, supplier_evaluations tables

Revision ID: 20260405_0005
Revises: 20260405_0004
Create Date: 2026-04-05 03:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260405_0005"
down_revision = "20260405_0004"
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
    # ── equipment_master ─────────────────────────────────────────────────────
    op.create_table(
        "equipment_master",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("equip_no", sa.Text(), nullable=False),
        sa.Column("equip_name", sa.Text(), nullable=False),
        sa.Column("location", sa.Text(), nullable=False, server_default=""),
        sa.Column("model_no", sa.Text(), nullable=False, server_default=""),
        sa.Column("serial_no", sa.Text(), nullable=False, server_default=""),
        sa.Column("brand", sa.Text(), nullable=False, server_default=""),
        sa.Column("interval_days", sa.Integer(), nullable=False, server_default="90"),
        sa.Column("maint_items", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        *audit_columns(),
    )
    op.create_index("ix_equipment_master_equip_no", "equipment_master", ["equip_no"], unique=True)

    # ── maintenance_records ───────────────────────────────────────────────────
    op.create_table(
        "maintenance_records",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column(
            "equipment_id", sa.Text(),
            sa.ForeignKey("equipment_master.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("maint_date", sa.Text(), nullable=False),
        sa.Column("performed_by", sa.Text(), nullable=False, server_default=""),
        sa.Column("items_done", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("result", sa.Text(), nullable=False, server_default="正常"),
        sa.Column("remarks", sa.Text(), nullable=False, server_default=""),
        *audit_columns(),
    )
    op.create_index("ix_maintenance_records_equipment_id", "maintenance_records", ["equipment_id"])

    # ── supplier_evaluations ──────────────────────────────────────────────────
    op.create_table(
        "supplier_evaluations",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column(
            "supplier_id", sa.Text(),
            sa.ForeignKey("suppliers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("eval_date", sa.Text(), nullable=False),
        sa.Column("eval_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("eval_result", sa.Text(), nullable=False, server_default="合格"),
        sa.Column("eval_by", sa.Text(), nullable=False, server_default=""),
        sa.Column("issues", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("remarks", sa.Text(), nullable=False, server_default=""),
        sa.Column("next_eval_date", sa.Text(), nullable=True),
        *audit_columns(),
    )
    op.create_index("ix_supplier_evaluations_supplier_id", "supplier_evaluations", ["supplier_id"])


def downgrade() -> None:
    op.drop_index("ix_supplier_evaluations_supplier_id", table_name="supplier_evaluations")
    op.drop_table("supplier_evaluations")
    op.drop_index("ix_maintenance_records_equipment_id", table_name="maintenance_records")
    op.drop_table("maintenance_records")
    op.drop_index("ix_equipment_master_equip_no", table_name="equipment_master")
    op.drop_table("equipment_master")
