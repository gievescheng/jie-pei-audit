from __future__ import annotations

from fastapi import APIRouter

from . import auth, bom, customers, health, inventory, orders, products, shipments, suppliers

router = APIRouter(prefix="/api", tags=["erp-qms-core"])

router.include_router(health.router)
router.include_router(auth.router)
router.include_router(customers.router)
router.include_router(suppliers.router)
router.include_router(products.router)
router.include_router(bom.router)
router.include_router(orders.router)
router.include_router(inventory.router)
router.include_router(shipments.router)
