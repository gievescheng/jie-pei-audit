from __future__ import annotations

from .enums import OrderStatus, ShipmentStatus, WorkOrderStatus

# Valid next states for each current state.
# An empty set means the status is terminal.

SALES_ORDER_TRANSITIONS: dict[str, set[str]] = {
    OrderStatus.DRAFT:      {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
    OrderStatus.CONFIRMED:  {OrderStatus.RELEASED,  OrderStatus.CANCELLED},
    OrderStatus.RELEASED:   {OrderStatus.COMPLETED, OrderStatus.CANCELLED},
    OrderStatus.COMPLETED:  set(),
    OrderStatus.CANCELLED:  set(),
}

WORK_ORDER_TRANSITIONS: dict[str, set[str]] = {
    WorkOrderStatus.DRAFT:       {WorkOrderStatus.IN_PROGRESS, WorkOrderStatus.CANCELLED},
    WorkOrderStatus.IN_PROGRESS: {WorkOrderStatus.COMPLETED,   WorkOrderStatus.CANCELLED},
    WorkOrderStatus.COMPLETED:   set(),
    WorkOrderStatus.CANCELLED:   set(),
}

SHIPMENT_TRANSITIONS: dict[str, set[str]] = {
    ShipmentStatus.DRAFT:     {ShipmentStatus.SHIPPED,    ShipmentStatus.CANCELLED},
    ShipmentStatus.SHIPPED:   {ShipmentStatus.CONFIRMED},
    ShipmentStatus.CONFIRMED: set(),
    ShipmentStatus.CANCELLED: set(),
}
