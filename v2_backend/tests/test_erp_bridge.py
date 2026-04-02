"""Unit tests for v2_backend ERP bridge resolvers and schemas.

Covers:
  - adapters.py   — resolve_user / resolve_department / resolve_customer / resolve_supplier
  - schemas.py    — AuditLogResponse, DocumentResponse, AuditCacheResponse, CompareCacheResponse
  - config.py     — erp_base_url setting is present

No external services, no DB, no httpx real calls.
HTTP strategy is tested via unittest.mock patching httpx.get.
"""
from __future__ import annotations

import sys
import os
import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

# Ensure v2_backend importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestResolveUserNoneInput(unittest.TestCase):
    def setUp(self):
        from app.adapters import resolve_user
        self.resolve = resolve_user

    def test_none_returns_none(self):
        self.assertIsNone(self.resolve(None))

    def test_empty_string_returns_none(self):
        self.assertIsNone(self.resolve(""))


class TestResolveUserStubMode(unittest.TestCase):
    """No erp_base_url, no session → stub response."""

    def setUp(self):
        from app.adapters import resolve_user
        self.resolve = resolve_user

    def test_stub_returns_dict(self):
        result = self.resolve("some-uuid-001")
        self.assertIsInstance(result, dict)

    def test_stub_contains_id(self):
        result = self.resolve("some-uuid-001")
        self.assertEqual(result["id"], "some-uuid-001")

    def test_stub_resolved_is_false(self):
        result = self.resolve("some-uuid-001")
        self.assertFalse(result["resolved"])

    def test_stub_does_not_raise(self):
        try:
            self.resolve("any-value-here")
        except Exception as e:
            self.fail(f"resolve_user raised unexpectedly: {e}")


class TestResolveUserHTTPStrategy(unittest.TestCase):
    """HTTP strategy: mock httpx.get to verify adapter behaviour."""

    def setUp(self):
        from app.adapters import resolve_user
        self.resolve = resolve_user

    def test_http_success_returns_api_json(self):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "id": "user-uuid-123",
            "full_name": "王品管",
            "email": "qm@jepe.com",
        }
        with patch("app.adapters.httpx.get", return_value=mock_response) as mock_get:
            result = self.resolve("user-uuid-123", erp_base_url="http://erp.local:8000")
        mock_get.assert_called_once_with("http://erp.local:8000/api/users/user-uuid-123", timeout=5)
        self.assertEqual(result["full_name"], "王品管")

    def test_http_failure_returns_error_dict(self):
        with patch("app.adapters.httpx.get", side_effect=Exception("connection refused")):
            result = self.resolve("user-uuid-456", erp_base_url="http://erp.local:8000")
        self.assertIsNotNone(result)
        self.assertFalse(result["resolved"])
        self.assertIn("error", result)

    def test_http_none_input_skips_call(self):
        with patch("app.adapters.httpx.get") as mock_get:
            result = self.resolve(None, erp_base_url="http://erp.local:8000")
        mock_get.assert_not_called()
        self.assertIsNone(result)


class TestResolveDepartment(unittest.TestCase):
    def setUp(self):
        from app.adapters import resolve_department
        self.resolve = resolve_department

    def test_none_returns_none(self):
        self.assertIsNone(self.resolve(None))

    def test_stub_mode(self):
        result = self.resolve("dept-uuid-001")
        self.assertEqual(result["id"], "dept-uuid-001")
        self.assertFalse(result["resolved"])

    def test_http_success(self):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"id": "dept-uuid-001", "name": "品保部", "code": "QA"}
        with patch("app.adapters.httpx.get", return_value=mock_response):
            result = self.resolve("dept-uuid-001", erp_base_url="http://erp.local:8000")
        self.assertEqual(result["name"], "品保部")

    def test_http_failure_does_not_raise(self):
        with patch("app.adapters.httpx.get", side_effect=ConnectionError("timeout")):
            result = self.resolve("dept-uuid-001", erp_base_url="http://erp.local:8000")
        self.assertFalse(result["resolved"])


class TestResolveCustomer(unittest.TestCase):
    def setUp(self):
        from app.adapters import resolve_customer
        self.resolve = resolve_customer

    def test_none_returns_none(self):
        self.assertIsNone(self.resolve(None))

    def test_stub_mode(self):
        result = self.resolve("cust-uuid-001")
        self.assertEqual(result["id"], "cust-uuid-001")
        self.assertFalse(result["resolved"])

    def test_http_success(self):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "id": "cust-uuid-001", "name": "ABC Electronics", "contact_person": "李小明"
        }
        with patch("app.adapters.httpx.get", return_value=mock_response):
            result = self.resolve("cust-uuid-001", erp_base_url="http://erp.local:8000")
        self.assertEqual(result["contact_person"], "李小明")

    def test_url_format(self):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {}
        with patch("app.adapters.httpx.get", return_value=mock_response) as mock_get:
            self.resolve("cust-id-xyz", erp_base_url="http://erp.local:8000")
        mock_get.assert_called_once_with("http://erp.local:8000/api/customers/cust-id-xyz", timeout=5)


class TestResolveSupplier(unittest.TestCase):
    def setUp(self):
        from app.adapters import resolve_supplier
        self.resolve = resolve_supplier

    def test_none_returns_none(self):
        self.assertIsNone(self.resolve(None))

    def test_stub_mode(self):
        result = self.resolve("sup-uuid-001")
        self.assertEqual(result["id"], "sup-uuid-001")
        self.assertFalse(result["resolved"])

    def test_http_success(self):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "id": "sup-uuid-001", "name": "XYZ 原料", "category": "化工"
        }
        with patch("app.adapters.httpx.get", return_value=mock_response):
            result = self.resolve("sup-uuid-001", erp_base_url="http://erp.local:8000")
        self.assertEqual(result["category"], "化工")

    def test_url_format(self):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {}
        with patch("app.adapters.httpx.get", return_value=mock_response) as mock_get:
            self.resolve("sup-id-abc", erp_base_url="http://erp.local:8000")
        mock_get.assert_called_once_with("http://erp.local:8000/api/suppliers/sup-id-abc", timeout=5)


class TestBridgeResponseSchemas(unittest.TestCase):
    """Pydantic schemas for ERP-enriched responses."""

    def setUp(self):
        self.now = datetime.now(timezone.utc)

    def test_audit_log_response_minimal(self):
        from app.schemas import AuditLogResponse
        r = AuditLogResponse(
            id="al-001", trace_id="tr-001", task_type="document_audit",
            user_id="u1", prompt_version="v1.0", result_status="success",
            request_summary="test", created_at=self.now,
        )
        self.assertIsNone(r.auditor_id)
        self.assertIsNone(r.auditor_info)

    def test_audit_log_response_with_erp_fields(self):
        from app.schemas import AuditLogResponse
        r = AuditLogResponse(
            id="al-002", trace_id="tr-002", task_type="document_audit",
            user_id="u1", prompt_version="v1.0", result_status="success",
            request_summary="test", created_at=self.now,
            auditor_id="user-uuid-abc",
            auditor_info={"id": "user-uuid-abc", "full_name": "王品管", "resolved": True},
        )
        self.assertEqual(r.auditor_id, "user-uuid-abc")
        self.assertEqual(r.auditor_info["full_name"], "王品管")

    def test_document_response_minimal(self):
        from app.schemas import DocumentResponse
        r = DocumentResponse(
            id="doc-001", source_path="/docs/test.pdf", title="Test",
            document_code="DC001", file_type="pdf", version="1.0",
            owner_dept="QA", source_system="local", status="active",
            created_at=self.now, updated_at=self.now,
        )
        self.assertIsNone(r.owner_dept_id)
        self.assertIsNone(r.department_info)

    def test_document_response_with_erp_fields(self):
        from app.schemas import DocumentResponse
        r = DocumentResponse(
            id="doc-002", source_path="/docs/iso.pdf", title="ISO Manual",
            document_code="QM-001", file_type="pdf", version="2.0",
            owner_dept="品保部", source_system="local", status="active",
            created_at=self.now, updated_at=self.now,
            owner_dept_id="dept-uuid-qa",
            department_info={"id": "dept-uuid-qa", "name": "品保部", "code": "QA", "resolved": True},
        )
        self.assertEqual(r.owner_dept_id, "dept-uuid-qa")
        self.assertEqual(r.department_info["code"], "QA")

    def test_audit_cache_response_minimal(self):
        from app.schemas import AuditCacheResponse
        r = AuditCacheResponse(
            id="ac-001", cache_key="ck-001", document_id="doc-001",
            llm_enabled=False, created_at=self.now,
        )
        self.assertIsNone(r.customer_id)
        self.assertIsNone(r.customer_info)

    def test_audit_cache_response_with_erp_fields(self):
        from app.schemas import AuditCacheResponse
        r = AuditCacheResponse(
            id="ac-002", cache_key="ck-002", document_id="doc-001",
            llm_enabled=True, created_at=self.now,
            customer_id="cust-uuid-001",
            customer_info={"id": "cust-uuid-001", "name": "ABC Corp", "resolved": True},
        )
        self.assertEqual(r.customer_id, "cust-uuid-001")
        self.assertTrue(r.customer_info["resolved"])

    def test_compare_cache_response_minimal(self):
        from app.schemas import CompareCacheResponse
        r = CompareCacheResponse(
            id="cc-001", cache_key="ck-cc-001",
            left_document_id="doc-001", right_document_id="doc-002",
            use_llm=False, created_at=self.now,
        )
        self.assertIsNone(r.supplier_id)
        self.assertIsNone(r.supplier_info)

    def test_compare_cache_response_with_erp_fields(self):
        from app.schemas import CompareCacheResponse
        r = CompareCacheResponse(
            id="cc-002", cache_key="ck-cc-002",
            left_document_id="doc-001", right_document_id="doc-002",
            use_llm=True, created_at=self.now,
            supplier_id="sup-uuid-001",
            supplier_info={"id": "sup-uuid-001", "name": "XYZ材料", "resolved": True},
        )
        self.assertEqual(r.supplier_id, "sup-uuid-001")
        self.assertEqual(r.supplier_info["name"], "XYZ材料")


class TestERPBaseURLSetting(unittest.TestCase):
    """erp_base_url is present in Settings and defaults to None."""

    def test_erp_base_url_attribute_exists(self):
        from app.config import settings
        self.assertTrue(hasattr(settings, "erp_base_url"))

    def test_erp_base_url_default_is_none_when_env_not_set(self):
        # Remove env var if present so we test default
        original = os.environ.pop("ERP_BASE_URL", None)
        try:
            # Re-import to pick up current env
            from app.config import Settings
            s = Settings()
            self.assertIsNone(s.erp_base_url)
        finally:
            if original is not None:
                os.environ["ERP_BASE_URL"] = original

    def test_erp_base_url_env_key_documented(self):
        # Settings is a frozen dataclass whose defaults are evaluated at import time.
        # The env-var key "ERP_BASE_URL" is documented in config.py; we verify the
        # setting exists and accepts a string value via the constructor override.
        from app.config import Settings
        s = Settings(erp_base_url="http://test-erp:9000")
        self.assertEqual(s.erp_base_url, "http://test-erp:9000")


if __name__ == "__main__":
    unittest.main()
