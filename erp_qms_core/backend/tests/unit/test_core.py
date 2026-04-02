"""Unit tests for erp_qms_core core utilities.

Covers (no DB required):
  - core/request_context.py — trace_id, actor ContextVar isolation
  - core/security.py        — hash_password, verify_password
  - core/responses.py       — ok() response structure
  - core/logging.py         — configure_logging, get_logger (smoke)
"""
from __future__ import annotations

import logging
import threading
import unittest


class TestRequestContext(unittest.TestCase):
    """ContextVar behaviour: values are per-execution-context."""

    def setUp(self):
        # Re-import each test to avoid state leakage between tests
        from erp_qms_core.backend.app.core import request_context as rc
        self.rc = rc

    def test_default_actor_is_anonymous(self):
        self.assertEqual(self.rc.get_actor(), "anonymous")

    def test_set_and_get_actor(self):
        self.rc.set_actor("test_user")
        self.assertEqual(self.rc.get_actor(), "test_user")
        # Restore
        self.rc.set_actor("anonymous")

    def test_set_none_actor_defaults_to_anonymous(self):
        self.rc.set_actor(None)  # type: ignore[arg-type]
        self.assertEqual(self.rc.get_actor(), "anonymous")

    def test_set_trace_id_with_explicit_value(self):
        tid = self.rc.set_trace_id("explicit-trace-001")
        self.assertEqual(tid, "explicit-trace-001")
        self.assertEqual(self.rc.get_trace_id(), "explicit-trace-001")

    def test_set_trace_id_auto_generates_uuid(self):
        tid = self.rc.set_trace_id()
        self.assertIsNotNone(tid)
        self.assertGreater(len(tid), 10)  # UUID-like string

    def test_get_trace_id_auto_creates_if_empty(self):
        # Force empty state by setting empty string
        self.rc._trace_id.set("")
        tid = self.rc.get_trace_id()
        self.assertIsNotNone(tid)
        self.assertGreater(len(tid), 0)

    def test_trace_ids_are_unique(self):
        t1 = self.rc.set_trace_id()
        t2 = self.rc.set_trace_id()
        self.assertNotEqual(t1, t2)

    def test_actor_isolation_across_threads(self):
        """Each thread sees its own actor value (ContextVar isolation)."""
        results = {}

        def thread_fn(name, actor):
            self.rc.set_actor(actor)
            import time
            time.sleep(0.01)
            results[name] = self.rc.get_actor()

        t1 = threading.Thread(target=thread_fn, args=("t1", "user_A"))
        t2 = threading.Thread(target=thread_fn, args=("t2", "user_B"))
        t1.start(); t2.start()
        t1.join(); t2.join()

        # Each thread should see its own actor
        self.assertEqual(results["t1"], "user_A")
        self.assertEqual(results["t2"], "user_B")


class TestSecurity(unittest.TestCase):
    """Password hashing and verification — no external dependencies."""

    def setUp(self):
        from erp_qms_core.backend.app.core.security import hash_password, verify_password
        self.hash_password = hash_password
        self.verify_password = verify_password

    def test_hash_is_deterministic(self):
        h1 = self.hash_password("secret123")
        h2 = self.hash_password("secret123")
        self.assertEqual(h1, h2)

    def test_hash_is_hex_string(self):
        h = self.hash_password("password")
        # SHA-256 → 64 hex chars
        self.assertEqual(len(h), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in h))

    def test_different_passwords_produce_different_hashes(self):
        h1 = self.hash_password("abc")
        h2 = self.hash_password("ABC")
        self.assertNotEqual(h1, h2)

    def test_verify_correct_password(self):
        hashed = self.hash_password("qms1234")
        self.assertTrue(self.verify_password("qms1234", hashed))

    def test_verify_wrong_password(self):
        hashed = self.hash_password("qms1234")
        self.assertFalse(self.verify_password("wrong_pass", hashed))

    def test_verify_empty_string_against_non_empty(self):
        hashed = self.hash_password("something")
        self.assertFalse(self.verify_password("", hashed))

    def test_hash_empty_string(self):
        h = self.hash_password("")
        self.assertEqual(len(h), 64)
        self.assertTrue(self.verify_password("", h))

    def test_unicode_password(self):
        h = self.hash_password("密碼測試123")
        self.assertTrue(self.verify_password("密碼測試123", h))
        self.assertFalse(self.verify_password("密碼測試124", h))


class TestResponses(unittest.TestCase):
    """ok() helper returns the expected envelope structure."""

    def setUp(self):
        from erp_qms_core.backend.app.core.responses import ok
        self.ok = ok

    def test_ok_success_flag(self):
        result = self.ok({"key": "value"})
        self.assertTrue(result["success"])

    def test_ok_data_passthrough(self):
        data = {"id": "123", "name": "Test"}
        result = self.ok(data)
        self.assertEqual(result["data"], data)

    def test_ok_default_message(self):
        result = self.ok({})
        self.assertEqual(result["message"], "OK")

    def test_ok_custom_message(self):
        result = self.ok({}, message="created")
        self.assertEqual(result["message"], "created")

    def test_ok_trace_id_present(self):
        result = self.ok({})
        self.assertIn("trace_id", result)
        self.assertIsNotNone(result["trace_id"])
        self.assertGreater(len(result["trace_id"]), 0)

    def test_ok_trace_ids_are_unique(self):
        r1 = self.ok({})
        r2 = self.ok({})
        self.assertNotEqual(r1["trace_id"], r2["trace_id"])

    def test_ok_with_list_data(self):
        result = self.ok([1, 2, 3])
        self.assertEqual(result["data"], [1, 2, 3])

    def test_ok_with_none_data(self):
        result = self.ok(None)
        self.assertIsNone(result["data"])
        self.assertTrue(result["success"])


class TestLogging(unittest.TestCase):
    """configure_logging and get_logger smoke tests — just verify they don't raise."""

    def test_configure_logging_does_not_raise(self):
        from erp_qms_core.backend.app.core.logging import configure_logging
        configure_logging("WARNING")  # should not raise

    def test_get_logger_returns_logger(self):
        from erp_qms_core.backend.app.core.logging import get_logger
        logger = get_logger("test.unit.core")
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, "test.unit.core")

    def test_get_logger_same_name_returns_same_instance(self):
        from erp_qms_core.backend.app.core.logging import get_logger
        l1 = get_logger("same.logger")
        l2 = get_logger("same.logger")
        self.assertIs(l1, l2)


if __name__ == "__main__":
    unittest.main()
