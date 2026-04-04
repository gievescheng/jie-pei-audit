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


class TestPasswordHash(unittest.TestCase):
    """bcrypt 雜湊行為驗證。"""

    def test_hash_and_verify_correct_password(self):
        from erp_qms_core.backend.app.core.security import hash_password, verify_password
        hashed = hash_password("correct-password")
        self.assertTrue(verify_password("correct-password", hashed))

    def test_wrong_password_fails(self):
        from erp_qms_core.backend.app.core.security import hash_password, verify_password
        hashed = hash_password("correct-password")
        self.assertFalse(verify_password("wrong-password", hashed))

    def test_empty_password_handled_safely(self):
        from erp_qms_core.backend.app.core.security import hash_password, verify_password
        hashed = hash_password("")
        self.assertTrue(verify_password("", hashed))
        self.assertFalse(verify_password("not-empty", hashed))

    def test_two_hashes_of_same_password_differ(self):
        """bcrypt 每次加鹽不同，兩次雜湊結果不應相同。"""
        from erp_qms_core.backend.app.core.security import hash_password
        h1 = hash_password("same-password")
        h2 = hash_password("same-password")
        self.assertNotEqual(h1, h2)

    def test_unicode_password(self):
        from erp_qms_core.backend.app.core.security import hash_password, verify_password
        hashed = hash_password("密碼測試123")
        self.assertTrue(verify_password("密碼測試123", hashed))
        self.assertFalse(verify_password("密碼測試124", hashed))


class TestJWT(unittest.TestCase):
    """JWT 簽發與驗證。測試前需設定 ERP_QMS_CORE_JWT_SECRET。"""

    def setUp(self):
        import os
        os.environ["ERP_QMS_CORE_JWT_SECRET"] = "test-secret-for-unit-test-only"

    def test_create_and_decode_token(self):
        from erp_qms_core.backend.app.core.security import create_token, decode_token
        payload = {"sub": "user-uuid-001", "role": "qm", "name": "測試使用者"}
        token = create_token(payload)
        decoded = decode_token(token)
        self.assertIsNotNone(decoded)
        self.assertEqual(decoded["sub"], "user-uuid-001")
        self.assertEqual(decoded["role"], "qm")

    def test_invalid_token_returns_none(self):
        from erp_qms_core.backend.app.core.security import decode_token
        self.assertIsNone(decode_token("not-a-valid-token"))
        self.assertIsNone(decode_token(""))

    def test_expired_token_returns_none(self):
        import datetime
        from erp_qms_core.backend.app.core.security import create_token, decode_token
        payload = {
            "sub": "user-uuid-002",
            "role": "qm",
            "exp": datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=1),
        }
        token = create_token(payload)
        self.assertIsNone(decode_token(token))


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
