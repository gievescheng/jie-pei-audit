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

_TABLE: dict[str, dict[str, set[str]]] = {
    "sales_order": SALES_ORDER_TRANSITIONS,
    "work_order":  WORK_ORDER_TRANSITIONS,
    "shipment":    SHIPMENT_TRANSITIONS,
}


def can_transition(entity_type: str, current: str, next_status: str) -> bool:
    """Return True if moving from *current* to *next_status* is allowed."""
    return next_status in _TABLE.get(entity_type, {}).get(current, set())


def allowed_next(entity_type: str, current: str) -> set[str]:
    """Return the set of valid next states for a given entity and current status."""
    return set(_TABLE.get(entity_type, {}).get(current, set()))
