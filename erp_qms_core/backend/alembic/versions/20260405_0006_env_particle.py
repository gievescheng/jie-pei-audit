"""add env_particle_records table

Revision ID: 20260405_0006
Revises: 20260405_0005
Create Date: 2026-04-05 04:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260405_0006"
down_revision = "20260405_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "env_particle_records",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("meas_date", sa.Text(), nullable=False, index=True),
        sa.Column("run", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("session", sa.Text(), nullable=False, server_default="\u4e0a\u5348"),
        sa.Column("n_samples", sa.Integer(), nullable=False, server_default="14"),
        sa.Column("ch1avg", sa.Float(), nullable=False, server_default="0"),
        sa.Column("ch1max", sa.Float(), nullable=False, server_default="0"),
        sa.Column("ch2avg", sa.Float(), nullable=False, server_default="0"),
        sa.Column("ch2max", sa.Float(), nullable=False, server_default="0"),
        sa.Column("ch3avg", sa.Float(), nullable=False, server_default="0"),
        sa.Column("ch3max", sa.Float(), nullable=False, server_default="0"),
        sa.Column("note", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.Text(), nullable=False, server_default="system"),
        sa.Column("updated_by", sa.Text(), nullable=False, server_default="system"),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )


def downgrade() -> None:
    op.drop_table("env_particle_records")
