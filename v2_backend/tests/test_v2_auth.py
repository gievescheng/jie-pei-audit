"""
v2_backend/tests/test_v2_auth.py
確認 INTERNAL_API_KEY 機制在有設定與未設定時的行為。
"""
from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from v2_backend.app.config import settings
from v2_backend.app.main import app


class V2ApiKeyTest(unittest.TestCase):

    def setUp(self):
        self._original_key = settings.internal_api_key
        self.client = TestClient(app, raise_server_exceptions=False)

    def tearDown(self):
        object.__setattr__(settings, "internal_api_key", self._original_key)

    def test_no_key_configured_allows_all_requests(self):
        """INTERNAL_API_KEY 未設定時，所有請求應正常通過（開發模式）。"""
        object.__setattr__(settings, "internal_api_key", "")
        resp = self.client.get("/api/v2/health")
        self.assertEqual(resp.status_code, 200)

    def test_wrong_key_returns_401(self):
        """設定了 INTERNAL_API_KEY 後，錯誤的 key 應回傳 401。"""
        object.__setattr__(settings, "internal_api_key", "secret-key")
        resp = self.client.get("/api/v2/health", headers={"X-Api-Key": "wrong-key"})
        self.assertEqual(resp.status_code, 401)

    def test_correct_key_passes(self):
        """設定了 INTERNAL_API_KEY 後，正確的 key 應正常通過。"""
        object.__setattr__(settings, "internal_api_key", "secret-key")
        resp = self.client.get("/api/v2/health", headers={"X-Api-Key": "secret-key"})
        self.assertEqual(resp.status_code, 200)

    def test_missing_header_returns_401(self):
        """設定了 INTERNAL_API_KEY 後，缺少 header 應回傳 401。"""
        object.__setattr__(settings, "internal_api_key", "secret-key")
        resp = self.client.get("/api/v2/health")
        self.assertEqual(resp.status_code, 401)


if __name__ == "__main__":
    unittest.main()
