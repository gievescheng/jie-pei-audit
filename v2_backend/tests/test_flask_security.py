from __future__ import annotations

import unittest

from server import app


class FlaskSecurityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()

    def test_server_source_is_not_public(self):
        response = self.client.get("/server.py")
        self.assertEqual(response.status_code, 404)
        response.close()

    def test_private_runtime_config_is_not_public(self):
        response = self.client.get("/.v2_runtime.json")
        self.assertEqual(response.status_code, 404)
        response.close()

    def test_vendor_file_remains_public(self):
        response = self.client.get("/vendor/react.production.min.js")
        self.assertEqual(response.status_code, 200)
        response.close()


if __name__ == "__main__":
    unittest.main()
