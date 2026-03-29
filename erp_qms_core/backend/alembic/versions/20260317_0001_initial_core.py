"""initial ERP-QMS core schema

Revision ID: 20260317_0001
Revises:
Create Date: 2026-03-17 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260317_0001"
down_revision = None
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
        "departments",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("dept_code", sa.Text(), nullable=False),
        sa.Column("dept_name", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        *audit_columns(),
    )
    op.create_index("ix_departments_dept_code", "departments", ["dept_code"], unique=True)

    op.create_table(
        "roles",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("role_code", sa.Text(), nullable=False),
        sa.Column("role_name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        *audit_columns(),
    )
    op.create_index("ix_roles_role_code", "roles", ["role_code"], unique=True)

    op.create_table(
        "role_permissions",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("role_id", sa.Text(), sa.ForeignKey("roles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("permission_code", sa.Text(), nullable=False),
        sa.Column("permission_name", sa.Text(), nullable=False, server_default=""),
        *audit_columns(),
        sa.UniqueConstraint("role_id", "permission_code", name="uq_role_permission"),
    )
    op.create_index("ix_role_permissions_role_id", "role_permissions", ["role_id"], unique=False)
    op.create_index("ix_role_permissions_permission_code", "role_permissions", ["permission_code"], unique=False)

    op.create_table(
        "users",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("emp_no", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("dept_id", sa.Text(), sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("role_id", sa.Text(), sa.ForeignKey("roles.id"), nullable=True),
        sa.Column("email", sa.Text(), nullable=False, server_default=""),
        sa.Column("password_hash", sa.Text(), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        *audit_columns(),
    )
    op.create_index("ix_users_emp_no", "users", ["emp_no"], unique=True)

    op.create_table(
        "customers",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("customer_code", sa.Text(), nullable=False),
        sa.Column("customer_name", sa.Text(), nullable=False),
        sa.Column("short_name", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        *audit_columns(),
    )
    op.create_index("ix_customers_customer_code", "customers", ["customer_code"], unique=True)

    op.create_table(
        "suppliers",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("supplier_code", sa.Text(), nullable=False),
        sa.Column("supplier_name", sa.Text(), nullable=False),
        sa.Column("category", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        *audit_columns(),
    )
    op.create_index("ix_suppliers_supplier_code", "suppliers", ["supplier_code"], unique=True)

    op.create_table(
        "products",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("product_code", sa.Text(), nullable=False),
        sa.Column("product_name", sa.Text(), nullable=False),
        sa.Column("customer_part_no", sa.Text(), nullable=False, server_default=""),
        sa.Column("internal_part_no", sa.Text(), nullable=False, server_default=""),
        sa.Column("spec_summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        *audit_columns(),
    )
    op.create_index("ix_products_product_code", "products", ["product_code"], unique=True)

    op.create_table(
        "product_process_routes",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("product_id", sa.Text(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("route_code", sa.Text(), nullable=False),
        sa.Column("station_name", sa.Text(), nullable=False),
        sa.Column("sequence_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("need_param_check", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("need_inspection", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        *audit_columns(),
    )
    op.create_index("ix_product_process_routes_product_id", "product_process_routes", ["product_id"], unique=False)
    op.create_index("ix_product_process_routes_route_code", "product_process_routes", ["route_code"], unique=False)

    op.create_table(
        "material_master",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("material_code", sa.Text(), nullable=False),
        sa.Column("material_name", sa.Text(), nullable=False),
        sa.Column("material_type", sa.Text(), nullable=False, server_default="raw"),
        sa.Column("unit", sa.Text(), nullable=False, server_default="PCS"),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        *audit_columns(),
    )
    op.create_index("ix_material_master_material_code", "material_master", ["material_code"], unique=True)

    op.create_table(
        "bom_items",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("product_id", sa.Text(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("material_id", sa.Text(), sa.ForeignKey("material_master.id", ondelete="CASCADE"), nullable=False),
        sa.Column("qty_per", sa.Numeric(18, 4), nullable=False, server_default="1"),
        sa.Column("loss_rate", sa.Numeric(18, 4), nullable=False, server_default="0"),
        *audit_columns(),
    )

    op.create_table(
        "inventory_locations",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("location_code", sa.Text(), nullable=False),
        sa.Column("location_name", sa.Text(), nullable=False),
        sa.Column("location_type", sa.Text(), nullable=False, server_default="warehouse"),
        sa.Column("is_hold_area", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        *audit_columns(),
    )
    op.create_index("ix_inventory_locations_location_code", "inventory_locations", ["location_code"], unique=True)

    op.create_table(
        "shift_master",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("shift_code", sa.Text(), nullable=False),
        sa.Column("shift_name", sa.Text(), nullable=False),
        sa.Column("start_time", sa.Text(), nullable=False, server_default="08:00"),
        sa.Column("end_time", sa.Text(), nullable=False, server_default="17:00"),
        *audit_columns(),
    )
    op.create_index("ix_shift_master_shift_code", "shift_master", ["shift_code"], unique=True)

    op.create_table(
        "sales_orders",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("so_no", sa.Text(), nullable=False),
        sa.Column("customer_id", sa.Text(), sa.ForeignKey("customers.id"), nullable=True),
        sa.Column("order_date", sa.Date(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("order_status", sa.Text(), nullable=False, server_default="draft"),
        sa.Column("special_requirement", sa.Text(), nullable=False, server_default=""),
        *audit_columns(),
    )
    op.create_index("ix_sales_orders_so_no", "sales_orders", ["so_no"], unique=True)

    op.create_table(
        "sales_order_items",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("so_id", sa.Text(), sa.ForeignKey("sales_orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.Text(), sa.ForeignKey("products.id"), nullable=True),
        sa.Column("ordered_qty", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("unit", sa.Text(), nullable=False, server_default="PCS"),
        sa.Column("remark", sa.Text(), nullable=False, server_default=""),
        *audit_columns(),
    )

    op.create_table(
        "work_orders",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("wo_no", sa.Text(), nullable=False),
        sa.Column("so_id", sa.Text(), sa.ForeignKey("sales_orders.id"), nullable=True),
        sa.Column("product_id", sa.Text(), sa.ForeignKey("products.id"), nullable=True),
        sa.Column("planned_qty", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("released_qty", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("good_qty", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("ng_qty", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("wo_status", sa.Text(), nullable=False, server_default="draft"),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("finish_date", sa.Date(), nullable=True),
        *audit_columns(),
    )
    op.create_index("ix_work_orders_wo_no", "work_orders", ["wo_no"], unique=True)

    op.create_table(
        "inventory_transactions",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("trx_no", sa.Text(), nullable=False),
        sa.Column("trx_type", sa.Text(), nullable=False),
        sa.Column("item_type", sa.Text(), nullable=False),
        sa.Column("item_ref_id", sa.Text(), nullable=False, server_default=""),
        sa.Column("lot_no", sa.Text(), nullable=False, server_default=""),
        sa.Column("qty", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("location_code", sa.Text(), nullable=False, server_default=""),
        sa.Column("inventory_status", sa.Text(), nullable=False, server_default="available"),
        sa.Column("trx_date", sa.Date(), nullable=True),
        *audit_columns(),
    )
    op.create_index("ix_inventory_transactions_trx_no", "inventory_transactions", ["trx_no"], unique=True)

    op.create_table(
        "shipments",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("shipment_no", sa.Text(), nullable=False),
        sa.Column("so_id", sa.Text(), sa.ForeignKey("sales_orders.id"), nullable=True),
        sa.Column("shipment_date", sa.Date(), nullable=True),
        sa.Column("ship_status", sa.Text(), nullable=False, server_default="draft"),
        sa.Column("remark", sa.Text(), nullable=False, server_default=""),
        *audit_columns(),
    )
    op.create_index("ix_shipments_shipment_no", "shipments", ["shipment_no"], unique=True)

    op.create_table(
        "approval_workflows",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("workflow_code", sa.Text(), nullable=False),
        sa.Column("module_name", sa.Text(), nullable=False),
        sa.Column("ref_id", sa.Text(), nullable=False, server_default=""),
        sa.Column("step_name", sa.Text(), nullable=False),
        sa.Column("approver_role_code", sa.Text(), nullable=False, server_default=""),
        sa.Column("approval_status", sa.Text(), nullable=False, server_default="pending"),
        *audit_columns(),
    )
    op.create_index("ix_approval_workflows_workflow_code", "approval_workflows", ["workflow_code"], unique=False)

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("trace_id", sa.Text(), nullable=False),
        sa.Column("module_name", sa.Text(), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("actor", sa.Text(), nullable=False, server_default="system"),
        sa.Column("ref_table", sa.Text(), nullable=False, server_default=""),
        sa.Column("ref_id", sa.Text(), nullable=False, server_default=""),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        *audit_columns(),
    )
    op.create_index("ix_audit_logs_trace_id", "audit_logs", ["trace_id"], unique=False)
    op.create_index("ix_audit_logs_module_name", "audit_logs", ["module_name"], unique=False)

    op.create_table(
        "notification_log",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("channel", sa.Text(), nullable=False),
        sa.Column("target", sa.Text(), nullable=False, server_default=""),
        sa.Column("subject", sa.Text(), nullable=False, server_default=""),
        sa.Column("delivery_status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column("ref_table", sa.Text(), nullable=False, server_default=""),
        sa.Column("ref_id", sa.Text(), nullable=False, server_default=""),
        *audit_columns(),
    )


def downgrade() -> None:
    for index_name, table_name in [
        ("ix_audit_logs_module_name", "audit_logs"),
        ("ix_audit_logs_trace_id", "audit_logs"),
        ("ix_approval_workflows_workflow_code", "approval_workflows"),
        ("ix_shipments_shipment_no", "shipments"),
        ("ix_inventory_transactions_trx_no", "inventory_transactions"),
        ("ix_work_orders_wo_no", "work_orders"),
        ("ix_sales_orders_so_no", "sales_orders"),
        ("ix_shift_master_shift_code", "shift_master"),
        ("ix_inventory_locations_location_code", "inventory_locations"),
        ("ix_material_master_material_code", "material_master"),
        ("ix_product_process_routes_route_code", "product_process_routes"),
        ("ix_product_process_routes_product_id", "product_process_routes"),
        ("ix_products_product_code", "products"),
        ("ix_suppliers_supplier_code", "suppliers"),
        ("ix_customers_customer_code", "customers"),
        ("ix_users_emp_no", "users"),
        ("ix_role_permissions_permission_code", "role_permissions"),
        ("ix_role_permissions_role_id", "role_permissions"),
        ("ix_roles_role_code", "roles"),
        ("ix_departments_dept_code", "departments"),
    ]:
        op.drop_index(index_name, table_name=table_name)

    for table_name in [
        "notification_log",
        "audit_logs",
        "approval_workflows",
        "shipments",
        "inventory_transactions",
        "work_orders",
        "sales_order_items",
        "sales_orders",
        "shift_master",
        "inventory_locations",
        "bom_items",
        "material_master",
        "product_process_routes",
        "products",
        "suppliers",
        "customers",
        "users",
        "role_permissions",
        "roles",
        "departments",
    ]:
        op.drop_table(table_name)
