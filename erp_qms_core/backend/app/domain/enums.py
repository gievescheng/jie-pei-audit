from __future__ import annotations

from enum import Enum


class EntityStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class MaterialType(str, Enum):
    RAW = "raw"
    SEMI = "semi"
    FINISHED = "finished"


class LocationType(str, Enum):
    WAREHOUSE = "warehouse"
    PRODUCTION = "production"
    HOLD = "hold"


class OrderStatus(str, Enum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    RELEASED = "released"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class WorkOrderStatus(str, Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ShipmentStatus(str, Enum):
    DRAFT = "draft"
    SHIPPED = "shipped"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class InventoryStatus(str, Enum):
    AVAILABLE = "available"
    HOLD = "hold"
    CONSUMED = "consumed"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
