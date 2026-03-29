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
        self.api = api_module
        self.db_module = db_module

    def tearDown(self):
        self.db_module.engine.dispose()
        self.tmpdir.cleanup()
        os.environ.pop("ERP_QMS_CORE_DATABASE_URL", None)

    # ── 基本健康 ────────────────────────────────────────────

    def test_health(self):
        response = self.api.health()
        self.assertTrue(response["success"])

    # ── 部門 CRUD ────────────────────────────────────────────

    def test_create_department(self):
        response = self.api.create_department(self.api.schemas.DepartmentCreate(dept_code="QA", dept_name="品質部"))
        self.assertTrue(response["success"])
        payload = self.api.list_departments()
        self.assertEqual(len(payload["data"]), 1)
        self.assertEqual(payload["data"][0]["dept_code"], "QA")

    def test_duplicate_department_returns_conflict(self):
        self.api.create_department(self.api.schemas.DepartmentCreate(dept_code="QA", dept_name="品質部"))
        with self.assertRaises(HTTPException) as ctx:
            self.api.create_department(self.api.schemas.DepartmentCreate(dept_code="QA", dept_name="重複部門"))
        self.assertEqual(ctx.exception.status_code, 409)

    # ── 客戶 GET by ID / PUT ─────────────────────────────────

    def test_get_and_update_customer(self):
        created = self.api.create_customer(self.api.schemas.CustomerCreate(customer_code="C001", customer_name="測試客戶"))["data"]
        fetched = self.api.get_customer(created["id"])["data"]
        self.assertEqual(fetched["customer_code"], "C001")
        updated = self.api.update_customer(created["id"], self.api.schemas.CustomerUpdate(customer_name="更新客戶", status="inactive"))["data"]
        self.assertEqual(updated["customer_name"], "更新客戶")
        self.assertEqual(updated["status"], "inactive")

    def test_get_customer_not_found(self):
        with self.assertRaises(HTTPException) as ctx:
            self.api.get_customer("nonexistent-id")
        self.assertEqual(ctx.exception.status_code, 404)

    # ── 供應商 GET by ID / PUT ───────────────────────────────

    def test_get_and_update_supplier(self):
        created = self.api.create_supplier(self.api.schemas.SupplierCreate(supplier_code="S001", supplier_name="測試供應商"))["data"]
        fetched = self.api.get_supplier(created["id"])["data"]
        self.assertEqual(fetched["supplier_code"], "S001")
        updated = self.api.update_supplier(created["id"], self.api.schemas.SupplierUpdate(category="化工"))["data"]
        self.assertEqual(updated["status"], "active")

    # ── 產品 GET by ID / PUT ─────────────────────────────────

    def test_get_and_update_product(self):
        created = self.api.create_product(self.api.schemas.ProductCreate(product_code="P001", product_name="測試產品", spec_summary="ISO spec"))["data"]
        fetched = self.api.get_product(created["id"])["data"]
        self.assertEqual(fetched["spec_summary"], "ISO spec")
        updated = self.api.update_product(created["id"], self.api.schemas.ProductUpdate(product_name="更新產品"))["data"]
        self.assertEqual(updated["product_name"], "更新產品")

    # ── 材料主檔 CRUD ────────────────────────────────────────

    def test_material_crud(self):
        created = self.api.create_material(self.api.schemas.MaterialMasterCreate(material_code="M001", material_name="IPA 清洗劑", unit="L"))["data"]
        self.assertEqual(created["material_code"], "M001")
        listed = self.api.list_materials()["data"]
        self.assertEqual(len(listed), 1)
        fetched = self.api.get_material(created["id"])["data"]
        self.assertEqual(fetched["unit"], "L")
        updated = self.api.update_material(created["id"], self.api.schemas.MaterialMasterUpdate(unit="KG"))["data"]
        self.assertEqual(updated["status"], "active")

    # ── BOM CRUD ─────────────────────────────────────────────

    def test_bom_crud(self):
        product = self.api.create_product(self.api.schemas.ProductCreate(product_code="P001", product_name="成品"))["data"]
        material = self.api.create_material(self.api.schemas.MaterialMasterCreate(material_code="M001", material_name="原料", unit="L"))["data"]
        added = self.api.add_bom_item(product["id"], self.api.schemas.BomItemCreate(material_id=material["id"], qty_per=2.5))["data"]
        self.assertEqual(float(added["qty_per"]), 2.5)
        bom_list = self.api.list_bom(product["id"])["data"]
        self.assertEqual(len(bom_list), 1)
        deleted = self.api.delete_bom_item(product["id"], added["id"])
        self.assertTrue(deleted["success"])

    # ── 班次 CRUD ────────────────────────────────────────────

    def test_shift_crud(self):
        created = self.api.create_shift(self.api.schemas.ShiftMasterCreate(shift_code="A", shift_name="早班", start_time="08:00", end_time="17:00"))["data"]
        self.assertEqual(created["shift_code"], "A")
        listed = self.api.list_shifts()["data"]
        self.assertEqual(len(listed), 1)

    # ── 訂單完整流程（含明細、狀態更新）───────────────────────

    def test_sales_order_full_flow(self):
        customer = self.api.create_customer(self.api.schemas.CustomerCreate(customer_code="C001", customer_name="測試客戶"))["data"]
        product = self.api.create_product(self.api.schemas.ProductCreate(product_code="P001", product_name="測試產品"))["data"]
        so = self.api.create_sales_order(self.api.schemas.SalesOrderCreate(so_no="SO-001", customer_id=customer["id"]))["data"]
        # 新增訂單明細
        item = self.api.add_sales_order_item(so["id"], self.api.schemas.SalesOrderItemCreate(product_id=product["id"], ordered_qty=100))["data"]
        self.assertEqual(float(item["ordered_qty"]), 100)
        # GET by ID 包含明細
        detail = self.api.get_sales_order(so["id"])["data"]
        self.assertEqual(len(detail["items"]), 1)
        # 更新狀態
        updated = self.api.update_sales_order_status(so["id"], self.api.schemas.StatusUpdate(status="confirmed"))["data"]
        self.assertEqual(updated["order_status"], "confirmed")

    def test_create_sales_order_rejects_missing_customer(self):
        with self.assertRaises(HTTPException) as ctx:
            self.api.create_sales_order(
                self.api.schemas.SalesOrderCreate(so_no="SO-404", customer_id="missing-id", order_status="released")
            )
        self.assertEqual(ctx.exception.status_code, 422)

    # ── 工單完整流程 ─────────────────────────────────────────

    def test_work_order_full_flow(self):
        customer = self.api.create_customer(self.api.schemas.CustomerCreate(customer_code="C001", customer_name="測試客戶"))["data"]
        so = self.api.create_sales_order(self.api.schemas.SalesOrderCreate(so_no="SO-001", customer_id=customer["id"]))["data"]
        wo = self.api.create_work_order(self.api.schemas.WorkOrderCreate(wo_no="WO-001", so_id=so["id"], planned_qty=100))["data"]
        # GET by ID
        detail = self.api.get_work_order(wo["id"])["data"]
        self.assertEqual(float(detail["planned_qty"]), 100)
        # 更新狀態
        self.api.update_work_order_status(wo["id"], self.api.schemas.StatusUpdate(status="in_progress"))
        # 回報良品/不良品
        qty = self.api.update_work_order_qty(wo["id"], self.api.schemas.WorkOrderQtyUpdate(good_qty=95, ng_qty=5))["data"]
        self.assertEqual(float(qty["good_qty"]), 95)
        self.assertEqual(float(qty["ng_qty"]), 5)

    # ── 庫存異動 ─────────────────────────────────────────────

    def test_inventory_transaction(self):
        from datetime import date
        created = self.api.create_transaction(self.api.schemas.InventoryTransactionCreate(
            trx_no="TRX-001", trx_type="receipt", item_type="material",
            lot_no="LOT-A", qty=50, location_code="WH-01", trx_date=date.today()
        ))["data"]
        self.assertEqual(float(created["qty"]), 50)
        listed = self.api.list_transactions()["data"]
        self.assertEqual(len(listed), 1)

    # ── 出貨 ─────────────────────────────────────────────────

    def test_shipment_full_flow(self):
        from datetime import date
        customer = self.api.create_customer(self.api.schemas.CustomerCreate(customer_code="C001", customer_name="測試客戶"))["data"]
        so = self.api.create_sales_order(self.api.schemas.SalesOrderCreate(so_no="SO-001", customer_id=customer["id"]))["data"]
        shipment = self.api.create_shipment(self.api.schemas.ShipmentCreate(
            shipment_no="SH-001", so_id=so["id"], shipment_date=date.today()
        ))["data"]
        self.assertEqual(shipment["ship_status"], "draft")
        # GET by ID
        detail = self.api.get_shipment(shipment["id"])["data"]
        self.assertEqual(detail["shipment_no"], "SH-001")
        # 更新狀態
        updated = self.api.update_shipment_status(shipment["id"], self.api.schemas.StatusUpdate(status="shipped"))["data"]
        self.assertEqual(updated["ship_status"], "shipped")
        # LIST
        listed = self.api.list_shipments()["data"]
        self.assertEqual(len(listed), 1)


if __name__ == "__main__":
    unittest.main()
