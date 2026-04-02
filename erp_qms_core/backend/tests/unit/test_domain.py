"""Unit tests for erp_qms_core domain layer.

Covers:
  - domain/enums.py   — Enum membership & string values
  - domain/transitions.py — can_transition(), allowed_next()
  - domain/rules.py   — convention assertions (no DB needed)
"""
from __future__ import annotations

import unittest

from erp_qms_core.backend.app.domain.enums import (
    ApprovalStatus,
    EntityStatus,
    InventoryStatus,
    LocationType,
    MaterialType,
    OrderStatus,
    ShipmentStatus,
    WorkOrderStatus,
)
from erp_qms_core.backend.app.domain.transitions import (
    SALES_ORDER_TRANSITIONS,
    SHIPMENT_TRANSITIONS,
    WORK_ORDER_TRANSITIONS,
    allowed_next,
    can_transition,
)


class TestEnums(unittest.TestCase):
    """Enum values must be stable strings used by DB columns."""

    def test_entity_status_values(self):
        self.assertEqual(EntityStatus.ACTIVE, "active")
        self.assertEqual(EntityStatus.INACTIVE, "inactive")
        # .value must equal the string stored in DB Text columns
        self.assertEqual(EntityStatus.ACTIVE.value, "active")
        self.assertEqual(EntityStatus.INACTIVE.value, "inactive")

    def test_order_status_all_members(self):
        expected = {"draft", "confirmed", "released", "completed", "cancelled"}
        actual = {s.value for s in OrderStatus}
        self.assertEqual(actual, expected)

    def test_work_order_status_all_members(self):
        expected = {"draft", "in_progress", "completed", "cancelled"}
        actual = {s.value for s in WorkOrderStatus}
        self.assertEqual(actual, expected)

    def test_shipment_status_all_members(self):
        expected = {"draft", "shipped", "confirmed", "cancelled"}
        actual = {s.value for s in ShipmentStatus}
        self.assertEqual(actual, expected)

    def test_inventory_status_all_members(self):
        expected = {"available", "hold", "consumed"}
        actual = {s.value for s in InventoryStatus}
        self.assertEqual(actual, expected)

    def test_approval_status_all_members(self):
        expected = {"pending", "approved", "rejected"}
        actual = {s.value for s in ApprovalStatus}
        self.assertEqual(actual, expected)

    def test_material_type_all_members(self):
        expected = {"raw", "semi", "finished"}
        actual = {s.value for s in MaterialType}
        self.assertEqual(actual, expected)

    def test_location_type_all_members(self):
        expected = {"warehouse", "production", "hold"}
        actual = {s.value for s in LocationType}
        self.assertEqual(actual, expected)


class TestSalesOrderTransitions(unittest.TestCase):
    """SALES_ORDER_TRANSITIONS maps must encode a strict linear progression."""

    def test_draft_can_confirm(self):
        self.assertTrue(can_transition("sales_order", "draft", "confirmed"))

    def test_draft_can_cancel(self):
        self.assertTrue(can_transition("sales_order", "draft", "cancelled"))

    def test_draft_cannot_skip_to_completed(self):
        self.assertFalse(can_transition("sales_order", "draft", "completed"))

    def test_confirmed_can_release(self):
        self.assertTrue(can_transition("sales_order", "confirmed", "released"))

    def test_confirmed_can_cancel(self):
        self.assertTrue(can_transition("sales_order", "confirmed", "cancelled"))

    def test_released_can_complete(self):
        self.assertTrue(can_transition("sales_order", "released", "completed"))

    def test_released_can_cancel(self):
        self.assertTrue(can_transition("sales_order", "released", "cancelled"))

    def test_completed_is_terminal(self):
        self.assertEqual(allowed_next("sales_order", "completed"), set())
        self.assertFalse(can_transition("sales_order", "completed", "draft"))

    def test_cancelled_is_terminal(self):
        self.assertEqual(allowed_next("sales_order", "cancelled"), set())

    def test_allowed_next_draft(self):
        result = allowed_next("sales_order", "draft")
        self.assertIn("confirmed", result)
        self.assertIn("cancelled", result)
        self.assertNotIn("completed", result)

    def test_all_statuses_covered_in_table(self):
        """Every OrderStatus value must appear as a key in the transition table."""
        for status in OrderStatus:
            self.assertIn(status, SALES_ORDER_TRANSITIONS,
                          f"OrderStatus.{status} missing from SALES_ORDER_TRANSITIONS")


class TestWorkOrderTransitions(unittest.TestCase):
    def test_draft_to_in_progress(self):
        self.assertTrue(can_transition("work_order", "draft", "in_progress"))

    def test_draft_cannot_jump_to_completed(self):
        self.assertFalse(can_transition("work_order", "draft", "completed"))

    def test_in_progress_to_completed(self):
        self.assertTrue(can_transition("work_order", "in_progress", "completed"))

    def test_in_progress_can_cancel(self):
        self.assertTrue(can_transition("work_order", "in_progress", "cancelled"))

    def test_completed_is_terminal(self):
        self.assertEqual(allowed_next("work_order", "completed"), set())

    def test_cancelled_is_terminal(self):
        self.assertEqual(allowed_next("work_order", "cancelled"), set())

    def test_all_statuses_covered_in_table(self):
        for status in WorkOrderStatus:
            self.assertIn(status, WORK_ORDER_TRANSITIONS,
                          f"WorkOrderStatus.{status} missing from WORK_ORDER_TRANSITIONS")


class TestShipmentTransitions(unittest.TestCase):
    def test_draft_to_shipped(self):
        self.assertTrue(can_transition("shipment", "draft", "shipped"))

    def test_draft_can_cancel(self):
        self.assertTrue(can_transition("shipment", "draft", "cancelled"))

    def test_shipped_to_confirmed(self):
        self.assertTrue(can_transition("shipment", "shipped", "confirmed"))

    def test_shipped_cannot_go_back_to_draft(self):
        self.assertFalse(can_transition("shipment", "shipped", "draft"))

    def test_confirmed_is_terminal(self):
        self.assertEqual(allowed_next("shipment", "confirmed"), set())

    def test_cancelled_is_terminal(self):
        self.assertEqual(allowed_next("shipment", "cancelled"), set())

    def test_all_statuses_covered_in_table(self):
        for status in ShipmentStatus:
            self.assertIn(status, SHIPMENT_TRANSITIONS,
                          f"ShipmentStatus.{status} missing from SHIPMENT_TRANSITIONS")


class TestTransitionsEdgeCases(unittest.TestCase):
    def test_unknown_entity_type_returns_false(self):
        self.assertFalse(can_transition("unknown_entity", "draft", "active"))

    def test_unknown_entity_type_allowed_next_returns_empty(self):
        self.assertEqual(allowed_next("unknown_entity", "draft"), set())

    def test_unknown_current_status_returns_false(self):
        self.assertFalse(can_transition("sales_order", "no_such_status", "confirmed"))

    def test_unknown_current_status_allowed_next_returns_empty(self):
        self.assertEqual(allowed_next("sales_order", "no_such_status"), set())

    def test_empty_string_entity_type_safe(self):
        self.assertFalse(can_transition("", "", ""))
        self.assertEqual(allowed_next("", ""), set())


if __name__ == "__main__":
    unittest.main()
