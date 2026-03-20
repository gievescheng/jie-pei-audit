from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    created_by: Mapped[str] = mapped_column(Text, default="system")
    updated_by: Mapped[str] = mapped_column(Text, default="system")
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)


class Department(TimestampMixin, Base):
    __tablename__ = "departments"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    dept_code: Mapped[str] = mapped_column(Text, unique=True, index=True)
    dept_name: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Role(TimestampMixin, Base):
    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    role_code: Mapped[str] = mapped_column(Text, unique=True, index=True)
    role_name: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text, default="")


class RolePermission(TimestampMixin, Base):
    __tablename__ = "role_permissions"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    role_id: Mapped[str] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), index=True)
    permission_code: Mapped[str] = mapped_column(Text, index=True)
    permission_name: Mapped[str] = mapped_column(Text, default="")

    role: Mapped[Role] = relationship()

    __table_args__ = (UniqueConstraint("role_id", "permission_code", name="uq_role_permission"),)


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    emp_no: Mapped[str] = mapped_column(Text, unique=True, index=True)
    name: Mapped[str] = mapped_column(Text)
    dept_id: Mapped[str | None] = mapped_column(ForeignKey("departments.id"), nullable=True)
    role_id: Mapped[str | None] = mapped_column(ForeignKey("roles.id"), nullable=True)
    email: Mapped[str] = mapped_column(Text, default="")
    password_hash: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Customer(TimestampMixin, Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_code: Mapped[str] = mapped_column(Text, unique=True, index=True)
    customer_name: Mapped[str] = mapped_column(Text)
    short_name: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(Text, default="active")


class Supplier(TimestampMixin, Base):
    __tablename__ = "suppliers"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    supplier_code: Mapped[str] = mapped_column(Text, unique=True, index=True)
    supplier_name: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(Text, default="active")


class Product(TimestampMixin, Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    product_code: Mapped[str] = mapped_column(Text, unique=True, index=True)
    product_name: Mapped[str] = mapped_column(Text)
    customer_part_no: Mapped[str] = mapped_column(Text, default="")
    internal_part_no: Mapped[str] = mapped_column(Text, default="")
    spec_summary: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(Text, default="active")


class ProductProcessRoute(TimestampMixin, Base):
    __tablename__ = "product_process_routes"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    route_code: Mapped[str] = mapped_column(Text, index=True)
    station_name: Mapped[str] = mapped_column(Text)
    sequence_no: Mapped[int] = mapped_column(Integer, default=1)
    need_param_check: Mapped[bool] = mapped_column(Boolean, default=False)
    need_inspection: Mapped[bool] = mapped_column(Boolean, default=False)


class MaterialMaster(TimestampMixin, Base):
    __tablename__ = "material_master"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    material_code: Mapped[str] = mapped_column(Text, unique=True, index=True)
    material_name: Mapped[str] = mapped_column(Text)
    material_type: Mapped[str] = mapped_column(Text, default="raw")
    unit: Mapped[str] = mapped_column(Text, default="PCS")
    status: Mapped[str] = mapped_column(Text, default="active")


class BomItem(TimestampMixin, Base):
    __tablename__ = "bom_items"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    material_id: Mapped[str] = mapped_column(ForeignKey("material_master.id", ondelete="CASCADE"), index=True)
    qty_per: Mapped[float] = mapped_column(Numeric(18, 4), default=1)
    loss_rate: Mapped[float] = mapped_column(Numeric(18, 4), default=0)


class InventoryLocation(TimestampMixin, Base):
    __tablename__ = "inventory_locations"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    location_code: Mapped[str] = mapped_column(Text, unique=True, index=True)
    location_name: Mapped[str] = mapped_column(Text)
    location_type: Mapped[str] = mapped_column(Text, default="warehouse")
    is_hold_area: Mapped[bool] = mapped_column(Boolean, default=False)


class ShiftMaster(TimestampMixin, Base):
    __tablename__ = "shift_master"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    shift_code: Mapped[str] = mapped_column(Text, unique=True, index=True)
    shift_name: Mapped[str] = mapped_column(Text)
    start_time: Mapped[str] = mapped_column(Text, default="08:00")
    end_time: Mapped[str] = mapped_column(Text, default="17:00")


class SalesOrder(TimestampMixin, Base):
    __tablename__ = "sales_orders"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    so_no: Mapped[str] = mapped_column(Text, unique=True, index=True)
    customer_id: Mapped[str | None] = mapped_column(ForeignKey("customers.id"), nullable=True)
    order_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    due_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    order_status: Mapped[str] = mapped_column(Text, default="draft")
    special_requirement: Mapped[str] = mapped_column(Text, default="")


class SalesOrderItem(TimestampMixin, Base):
    __tablename__ = "sales_order_items"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    so_id: Mapped[str] = mapped_column(ForeignKey("sales_orders.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[str | None] = mapped_column(ForeignKey("products.id"), nullable=True)
    ordered_qty: Mapped[float] = mapped_column(Numeric(18, 4), default=0)
    unit: Mapped[str] = mapped_column(Text, default="PCS")
    remark: Mapped[str] = mapped_column(Text, default="")


class WorkOrder(TimestampMixin, Base):
    __tablename__ = "work_orders"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    wo_no: Mapped[str] = mapped_column(Text, unique=True, index=True)
    so_id: Mapped[str | None] = mapped_column(ForeignKey("sales_orders.id"), nullable=True)
    product_id: Mapped[str | None] = mapped_column(ForeignKey("products.id"), nullable=True)
    planned_qty: Mapped[float] = mapped_column(Numeric(18, 4), default=0)
    released_qty: Mapped[float] = mapped_column(Numeric(18, 4), default=0)
    good_qty: Mapped[float] = mapped_column(Numeric(18, 4), default=0)
    ng_qty: Mapped[float] = mapped_column(Numeric(18, 4), default=0)
    wo_status: Mapped[str] = mapped_column(Text, default="draft")
    start_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    finish_date: Mapped[Date | None] = mapped_column(Date, nullable=True)


class InventoryTransaction(TimestampMixin, Base):
    __tablename__ = "inventory_transactions"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    trx_no: Mapped[str] = mapped_column(Text, unique=True, index=True)
    trx_type: Mapped[str] = mapped_column(Text)
    item_type: Mapped[str] = mapped_column(Text)
    item_ref_id: Mapped[str] = mapped_column(Text, default="")
    lot_no: Mapped[str] = mapped_column(Text, default="")
    qty: Mapped[float] = mapped_column(Numeric(18, 4), default=0)
    location_code: Mapped[str] = mapped_column(Text, default="")
    inventory_status: Mapped[str] = mapped_column(Text, default="available")
    trx_date: Mapped[Date | None] = mapped_column(Date, nullable=True)


class Shipment(TimestampMixin, Base):
    __tablename__ = "shipments"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    shipment_no: Mapped[str] = mapped_column(Text, unique=True, index=True)
    so_id: Mapped[str | None] = mapped_column(ForeignKey("sales_orders.id"), nullable=True)
    shipment_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    ship_status: Mapped[str] = mapped_column(Text, default="draft")
    remark: Mapped[str] = mapped_column(Text, default="")


class ApprovalWorkflow(TimestampMixin, Base):
    __tablename__ = "approval_workflows"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_code: Mapped[str] = mapped_column(Text, index=True)
    module_name: Mapped[str] = mapped_column(Text)
    ref_id: Mapped[str] = mapped_column(Text, default="")
    step_name: Mapped[str] = mapped_column(Text)
    approver_role_code: Mapped[str] = mapped_column(Text, default="")
    approval_status: Mapped[str] = mapped_column(Text, default="pending")


class AuditLog(TimestampMixin, Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    trace_id: Mapped[str] = mapped_column(Text, index=True)
    module_name: Mapped[str] = mapped_column(Text, index=True)
    action: Mapped[str] = mapped_column(Text)
    actor: Mapped[str] = mapped_column(Text, default="system")
    ref_table: Mapped[str] = mapped_column(Text, default="")
    ref_id: Mapped[str] = mapped_column(Text, default="")
    summary: Mapped[str] = mapped_column(Text, default="")


class NotificationLog(TimestampMixin, Base):
    __tablename__ = "notification_log"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    channel: Mapped[str] = mapped_column(Text)
    target: Mapped[str] = mapped_column(Text, default="")
    subject: Mapped[str] = mapped_column(Text, default="")
    delivery_status: Mapped[str] = mapped_column(Text, default="pending")
    ref_table: Mapped[str] = mapped_column(Text, default="")
    ref_id: Mapped[str] = mapped_column(Text, default="")
