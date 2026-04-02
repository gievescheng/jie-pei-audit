"""Add ERP bridge FK columns (auditor_id, owner_dept_id, customer_id, supplier_id)

Revision ID: 20260401_0002
Revises: 20260316_0001
Create Date: 2026-04-01 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260401_0002"
down_revision = "20260316_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # audit_logs → erp_qms_core.users
    op.add_column(
        "audit_logs",
        sa.Column(
            "auditor_id", sa.Text(), nullable=True,
            comment="FK to erp_qms_core.users.id",
        ),
    )
    op.create_index("ix_audit_logs_auditor_id", "audit_logs", ["auditor_id"])

    # documents → erp_qms_core.departments
    op.add_column(
        "documents",
        sa.Column(
            "owner_dept_id", sa.Text(), nullable=True,
            comment="FK to erp_qms_core.departments.id",
        ),
    )
    op.create_index("ix_documents_owner_dept_id", "documents", ["owner_dept_id"])

    # audit_cache → erp_qms_core.customers
    op.add_column(
        "audit_cache",
        sa.Column(
            "customer_id", sa.Text(), nullable=True,
            comment="FK to erp_qms_core.customers.id",
        ),
    )
    op.create_index("ix_audit_cache_customer_id", "audit_cache", ["customer_id"])

    # compare_cache → erp_qms_core.suppliers
    op.add_column(
        "compare_cache",
        sa.Column(
            "supplier_id", sa.Text(), nullable=True,
            comment="FK to erp_qms_core.suppliers.id",
        ),
    )
    op.create_index("ix_compare_cache_supplier_id", "compare_cache", ["supplier_id"])


def downgrade() -> None:
    op.drop_index("ix_compare_cache_supplier_id", table_name="compare_cache")
    op.drop_column("compare_cache", "supplier_id")

    op.drop_index("ix_audit_cache_customer_id", table_name="audit_cache")
    op.drop_column("audit_cache", "customer_id")

    op.drop_index("ix_documents_owner_dept_id", table_name="documents")
    op.drop_column("documents", "owner_dept_id")

    op.drop_index("ix_audit_logs_auditor_id", table_name="audit_logs")
    op.drop_column("audit_logs", "auditor_id")
