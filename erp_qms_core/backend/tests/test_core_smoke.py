from __future__ import annotations

import importlib
import os
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient


class ERPQMSCoreSmokeTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        db_path = Path(self.tmpdir.name) / "core.db"
        os.environ["ERP_QMS_CORE_DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"

        from app import config as config_module
        from app import db as db_module
        from app import models as models_module
        from app import main as main_module

        importlib.reload(config_module)
        importlib.reload(db_module)
        importlib.reload(models_module)
        importlib.reload(main_module)

        db_module.create_dev_schema()
        self.db_module = db_module
        self.client = TestClient(main_module.app)

    def tearDown(self):
        self.client.close()
        self.db_module.engine.dispose()
        self.tmpdir.cleanup()
        os.environ.pop("ERP_QMS_CORE_DATABASE_URL", None)

    def test_health(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

    def test_create_department(self):
        response = self.client.post("/api/master/departments", json={"dept_code": "QA", "dept_name": "品質部"})
        self.assertEqual(response.status_code, 200)
        list_response = self.client.get("/api/master/departments")
        payload = list_response.json()
        self.assertEqual(len(payload["data"]), 1)
        self.assertEqual(payload["data"][0]["dept_code"], "QA")

    def test_create_sales_order_and_work_order(self):
        customer = self.client.post("/api/master/customers", json={"customer_code": "C001", "customer_name": "測試客戶"}).json()["data"]
        sales_order = self.client.post(
            "/api/orders/sales-orders",
            json={"so_no": "SO-001", "customer_id": customer["id"], "order_status": "released"},
        ).json()["data"]
        work_order = self.client.post(
            "/api/orders/work-orders",
            json={"wo_no": "WO-001", "so_id": sales_order["id"], "planned_qty": 100, "wo_status": "released"},
        ).json()["data"]
        self.assertEqual(work_order["wo_no"], "WO-001")


if __name__ == "__main__":
    unittest.main()
