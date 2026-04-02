"""Workflow tests for erp_qms_core state transition engine.

These tests validate full lifecycle paths through the state machine —
not individual can_transition() calls, but end-to-end sequences that
mirror real business workflows.  No DB needed; pure domain logic.
"""
from __future__ import annotations

import unittest

from erp_qms_core.backend.app.domain.transitions import allowed_next, can_transition


class TestSalesOrderWorkflow(unittest.TestCase):
    """ISO 9001 §8.2 — Customer Requirements / Order Processing lifecycle."""

    def _walk(self, entity: str, path: list[str]) -> None:
        """Assert every consecutive step in `path` is a valid transition."""
        for i in range(len(path) - 1):
            current, nxt = path[i], path[i + 1]
            self.assertTrue(
                can_transition(entity, current, nxt),
                f"Expected {entity}: {current} → {nxt} to be valid",
            )

    def test_full_happy_path(self):
        """draft → confirmed → released → completed"""
        self._walk("sales_order", ["draft", "confirmed", "released", "completed"])

    def test_early_cancel_from_draft(self):
        """draft → cancelled"""
        self.assertTrue(can_transition("sales_order", "draft", "cancelled"))
        self.assertEqual(allowed_next("sales_order", "cancelled"), set())

    def test_cancel_after_confirm(self):
        """draft → confirmed → cancelled"""
        self._walk("sales_order", ["draft", "confirmed", "cancelled"])

    def test_cancel_after_release(self):
        """draft → confirmed → released → cancelled"""
        self._walk("sales_order", ["draft", "confirmed", "released", "cancelled"])

    def test_cannot_reopen_completed(self):
        for target in ("draft", "confirmed", "released", "cancelled"):
            self.assertFalse(
                can_transition("sales_order", "completed", target),
                f"completed should not transition to {target}",
            )

    def test_cannot_reopen_cancelled(self):
        for target in ("draft", "confirmed", "released", "completed"):
            self.assertFalse(
                can_transition("sales_order", "cancelled", target),
                f"cancelled should not transition to {target}",
            )

    def test_cannot_skip_confirmed(self):
        """draft cannot jump directly to released."""
        self.assertFalse(can_transition("sales_order", "draft", "released"))

    def test_cannot_skip_released(self):
        """confirmed cannot jump directly to completed."""
        self.assertFalse(can_transition("sales_order", "confirmed", "completed"))

    def test_all_intermediate_states_have_successors(self):
        intermediate = ["draft", "confirmed", "released"]
        for state in intermediate:
            self.assertGreater(
                len(allowed_next("sales_order", state)), 0,
                f"State '{state}' should have at least one allowed successor",
            )


class TestWorkOrderWorkflow(unittest.TestCase):
    """ISO 9001 §8.5 — Production / Service Provision lifecycle."""

    def test_full_happy_path(self):
        """draft → in_progress → completed"""
        self.assertTrue(can_transition("work_order", "draft", "in_progress"))
        self.assertTrue(can_transition("work_order", "in_progress", "completed"))

    def test_cancel_from_draft(self):
        self.assertTrue(can_transition("work_order", "draft", "cancelled"))

    def test_cancel_while_in_progress(self):
        self.assertTrue(can_transition("work_order", "in_progress", "cancelled"))

    def test_cannot_skip_in_progress(self):
        self.assertFalse(can_transition("work_order", "draft", "completed"))

    def test_completed_has_no_successors(self):
        self.assertEqual(allowed_next("work_order", "completed"), set())

    def test_cancelled_has_no_successors(self):
        self.assertEqual(allowed_next("work_order", "cancelled"), set())

    def test_cannot_go_back_to_draft_from_in_progress(self):
        self.assertFalse(can_transition("work_order", "in_progress", "draft"))

    def test_all_intermediate_states_have_successors(self):
        for state in ["draft", "in_progress"]:
            self.assertGreater(len(allowed_next("work_order", state)), 0)


class TestShipmentWorkflow(unittest.TestCase):
    """ISO 9001 §8.5.5 — Post-delivery / Shipment lifecycle."""

    def test_full_happy_path(self):
        """draft → shipped → confirmed"""
        self.assertTrue(can_transition("shipment", "draft", "shipped"))
        self.assertTrue(can_transition("shipment", "shipped", "confirmed"))

    def test_cancel_from_draft(self):
        self.assertTrue(can_transition("shipment", "draft", "cancelled"))

    def test_cannot_cancel_shipped(self):
        """Once shipped, cannot cancel (goods are in transit)."""
        self.assertFalse(can_transition("shipment", "shipped", "cancelled"))

    def test_cannot_go_back_from_shipped_to_draft(self):
        self.assertFalse(can_transition("shipment", "shipped", "draft"))

    def test_confirmed_is_terminal(self):
        self.assertEqual(allowed_next("shipment", "confirmed"), set())

    def test_cancelled_is_terminal(self):
        self.assertEqual(allowed_next("shipment", "cancelled"), set())

    def test_draft_has_two_options(self):
        opts = allowed_next("shipment", "draft")
        self.assertIn("shipped", opts)
        self.assertIn("cancelled", opts)

    def test_shipped_has_exactly_one_option(self):
        opts = allowed_next("shipment", "shipped")
        self.assertEqual(opts, {"confirmed"})


class TestCrossEntityGuards(unittest.TestCase):
    """Ensure transition logic does not leak across entity types."""

    def test_sales_order_transition_not_valid_for_work_order(self):
        # released is not a WorkOrderStatus — should not be a valid next state
        self.assertFalse(can_transition("work_order", "in_progress", "released"))

    def test_shipment_transition_not_valid_for_sales_order(self):
        self.assertFalse(can_transition("sales_order", "draft", "shipped"))

    def test_work_order_status_not_valid_for_shipment(self):
        self.assertFalse(can_transition("shipment", "draft", "in_progress"))


class TestAllowedNextReturnType(unittest.TestCase):
    """allowed_next() must always return a set (never None / list)."""

    def test_returns_set_for_valid_state(self):
        result = allowed_next("sales_order", "draft")
        self.assertIsInstance(result, set)

    def test_returns_set_for_terminal_state(self):
        result = allowed_next("sales_order", "completed")
        self.assertIsInstance(result, set)
        self.assertEqual(len(result), 0)

    def test_returns_set_for_unknown_entity(self):
        result = allowed_next("ghost_entity", "draft")
        self.assertIsInstance(result, set)
        self.assertEqual(len(result), 0)

    def test_returns_independent_copy(self):
        """Modifying returned set should not affect the transition table."""
        s1 = allowed_next("sales_order", "draft")
        s1.add("__test_pollution__")
        s2 = allowed_next("sales_order", "draft")
        self.assertNotIn("__test_pollution__", s2)


if __name__ == "__main__":
    unittest.main()
