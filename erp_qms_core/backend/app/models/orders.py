from __future__ import annotations

import uuid

from sqlalchemy import Date, ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db import Base
from .base import TimestampMixin


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
