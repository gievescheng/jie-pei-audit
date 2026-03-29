from __future__ import annotations

import importlib
import os
import tempfile
import unittest
from pathlib import Path

from fastapi import HTTPException


class ERPQMSCoreSmokeTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        db_path = Path(self.tmpdir.name) / "core.db"
        os.environ["ERP_QMS_CORE_DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"

        from erp_qms_core.backend.app import config as config_module
        from erp_qms_core.backend.app import api as api_module
        from erp_qms_core.backend.app import db as db_module
        from erp_qms_core.backend.app import models as models_module

        importlib.reload(config_module)
        importlib.reload(api_module)
        importlib.reload(db_module)
        importlib.reload(models_module)

        db_module.create_dev_schema()
        self.api_module = api_module
        self.db_module = db_module

    def tearDown(self):
        self.db_module.engine.dispose()
        self.tmpdir.cleanup()
        os.environ.pop("ERP_QMS_CORE_DATABASE_URL", None)

    def test_health(self):
        response = self.api_module.health()
        self.assertTrue(response["success"])

    def test_create_department(self):
        response = self.api_module.create_department(self.api_module.schemas.DepartmentCreate(dept_code="QA", dept_name="品質部"))
        self.assertTrue(response["success"])
        payload = self.api_module.list_departments()
        self.assertEqual(len(payload["data"]), 1)
        self.assertEqual(payload["data"][0]["dept_code"], "QA")

    def test_duplicate_department_returns_conflict(self):
        first = self.api_module.create_department(self.api_module.schemas.DepartmentCreate(dept_code="QA", dept_name="品質部"))
        self.assertTrue(first["success"])
        with self.assertRaises(HTTPException) as ctx:
            self.api_module.create_department(self.api_module.schemas.DepartmentCreate(dept_code="QA", dept_name="重複部門"))
        self.assertEqual(ctx.exception.status_code, 409)
        self.assertEqual(ctx.exception.detail, "resource already exists")

    def test_create_sales_order_and_work_order(self):
        customer = self.api_module.create_customer(
            self.api_module.schemas.CustomerCreate(customer_code="C001", customer_name="測試客戶")
        )["data"]
        sales_order = self.api_module.create_sales_order(
            self.api_module.schemas.SalesOrderCreate(so_no="SO-001", customer_id=customer["id"], order_status="released")
        )["data"]
        work_order = self.api_module.create_work_order(
            self.api_module.schemas.WorkOrderCreate(wo_no="WO-001", so_id=sales_order["id"], planned_qty=100, wo_status="released")
        )["data"]
        self.assertEqual(work_order["wo_no"], "WO-001")

    def test_create_sales_order_rejects_missing_customer(self):
        with self.assertRaises(HTTPException) as ctx:
            self.api_module.create_sales_order(
                self.api_module.schemas.SalesOrderCreate(so_no="SO-404", customer_id="missing-id", order_status="released")
            )
        self.assertEqual(ctx.exception.status_code, 422)
        self.assertEqual(ctx.exception.detail, "related resource does not exist")


if __name__ == "__main__":
    unittest.main()
