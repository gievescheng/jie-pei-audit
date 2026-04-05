"""add qms_documents table

Revision ID: 20260405_0003
Revises: 20260405_0002
Create Date: 2026-04-05 01:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260405_0003"
down_revision = "20260405_0002"
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
        "qms_documents",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("doc_no", sa.Text(), nullable=False),
        sa.Column("doc_name", sa.Text(), nullable=False),
        sa.Column("doc_type", sa.Text(), nullable=False, server_default="管理程序"),
        sa.Column("version", sa.Text(), nullable=False, server_default="1.0"),
        sa.Column("department", sa.Text(), nullable=False, server_default=""),
        sa.Column("author", sa.Text(), nullable=False, server_default=""),
        sa.Column("issue_date", sa.Text(), nullable=False, server_default=""),
        sa.Column("retention_years", sa.Integer(), nullable=False, server_default="16"),
        sa.Column("pdf_path", sa.Text(), nullable=False, server_default=""),
        sa.Column("docx_path", sa.Text(), nullable=False, server_default=""),
        sa.Column("remarks", sa.Text(), nullable=False, server_default=""),
        *audit_columns(),
    )
    op.create_index(
        "ix_qms_documents_doc_no",
        "qms_documents",
        ["doc_no"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_qms_documents_doc_no", table_name="qms_documents")
    op.drop_table("qms_documents")
