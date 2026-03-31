from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db import Base
from .base import TimestampMixin


class InventoryLocation(TimestampMixin, Base):
    __tablename__ = "inventory_locations"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    location_code: Mapped[str] = mapped_column(Text, unique=True, index=True)
    location_name: Mapped[str] = mapped_column(Text)
    location_type: Mapped[str] = mapped_column(Text, default="warehouse")
    is_hold_area: Mapped[bool] = mapped_column(Boolean, default=False)


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
