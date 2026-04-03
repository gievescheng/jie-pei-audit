"""Add compare_results table

Revision ID: 20260403_0003
Revises: 20260401_0002
Create Date: 2026-04-03 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260403_0003"
down_revision = "20260401_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "compare_results",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("left_document_id", sa.Text(), nullable=True),
        sa.Column("right_document_id", sa.Text(), nullable=True),
        sa.Column("left_title", sa.Text(), nullable=False, server_default=""),
        sa.Column("right_title", sa.Text(), nullable=False, server_default=""),
        sa.Column("similarity", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("added_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("removed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("conclusion_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.Text(), nullable=False, server_default="system"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_compare_results_left_document_id", "compare_results", ["left_document_id"])
    op.create_index("ix_compare_results_right_document_id", "compare_results", ["right_document_id"])


def downgrade() -> None:
    op.drop_index("ix_compare_results_right_document_id", table_name="compare_results")
    op.drop_index("ix_compare_results_left_document_id", table_name="compare_results")
    op.drop_table("compare_results")
