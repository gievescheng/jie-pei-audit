"""stub for previously applied migration

Revision ID: 20260328_0002
Revises: 20260317_0001
Create Date: 2026-03-28 00:00:00
"""
from __future__ import annotations

revision = "20260328_0002"
down_revision = "20260317_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # This migration was applied directly to the database.
    # The stub exists to maintain the Alembic revision chain.
    pass


def downgrade() -> None:
    pass
