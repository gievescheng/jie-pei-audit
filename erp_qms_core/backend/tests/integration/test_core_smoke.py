from __future__ import annotations

import os
import tempfile
import unittest
from datetime import date
from pathlib import Path

from fastapi import HTTPException


class ERPQMSCoreSmokeTest(unittest.TestCase):
    """
    Integration smoke tests.  Each test runs against a fresh in-memory SQLite
    database.  The lazy settings + reset_engine() pattern means no importlib
    reloading is needed.
    """

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        db_path = Path(self.tmpdir.name) / "core.db"
        os.environ["ERP_QMS_CORE_DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"

        from erp_qms_core.backend.app.core import db as db_module

        db_module.reset_engine()
        db_module.create_dev_schema()
        self.db = db_module

        from erp_qms_core.backend.app.services import master as master_svc
        from erp_qms_core.backend.app.services import customers, suppliers, products, bom
        from erp_qms_core.backend.app.services import sales_orders, work_orders
        from erp_qms_core.backend.app.services import inventory as inv_svc
        from erp_qms_core.backend.app.services import shipments

        self.master = master_svc
        self.customers = customers
        self.suppliers = suppliers
        self.products = products
        self.bom = bom
        self.so = sales_orders
        self.wo = work_orders
        self.inv = inv_svc
        self.ship = shipments

        from erp_qms_core.backend.app.schemas import (
            DepartmentCreate, RoleCreate,
            CustomerCreate, CustomerUpdate,
            SupplierCreate, SupplierUpdate,
            ProductCreate, ProductUpdate,
            MaterialMasterCreate, MaterialMasterUpdate,
            BomItemCreate,
            ShiftMasterCreate,
            SalesOrderCreate, SalesOrderItemCreate,
            WorkOrderCreate, WorkOrderQtyUpdate,
            InventoryLocationCreate, InventoryTransactionCreate,
            ShipmentCreate, StatusUpdate,
        )
        self.s = type("S", (), {
            "DepartmentCreate": DepartmentCreate,
            "RoleCreate": RoleCreate,
            "CustomerCreate": CustomerCreate,
            "CustomerUpdate": CustomerUpdate,
            "SupplierCreate": SupplierCreate,
            "SupplierUpdate": SupplierUpdate,
            "ProductCreate": ProductCreate,
            "ProductUpdate": ProductUpdate,
            "MaterialMasterCreate": MaterialMasterCreate,
            "MaterialMasterUpdate": MaterialMasterUpdate,
            "BomItemCreate": BomItemCreate,
            "ShiftMasterCreate": ShiftMasterCreate,
            "SalesOrderCreate": SalesOrderCreate,
            "SalesOrderItemCreate": SalesOrderItemCreate,
            "WorkOrderCreate": WorkOrderCreate,
            "WorkOrderQtyUpdate": WorkOrderQtyUpdate,
            "InventoryLocationCreate": InventoryLocationCreate,
            "InventoryTransactionCreate": InventoryTransactionCreate,
            "ShipmentCreate": ShipmentCreate,
            "StatusUpdate": StatusUpdate,
        })()

    def tearDown(self):
        self.db.reset_engine()
        self.tmpdir.cleanup()
        os.environ.pop("ERP_QMS_CORE_DATABASE_URL", None)

    # ── 基本健康 ────────────────────────────────────────────

    def test_health(self):
        from erp_qms_core.backend.app.core.responses import ok
        result = ok({"service": "jepe-erp-qms-core"}, message="healthy")
        self.assertTrue(result["success"])

    # ── 部門 CRUD ────────────────────────────────────────────

    def test_create_department(self):
        response = self.master.create_department(self.s.DepartmentCreate(dept_code="QA", dept_name="品質部"))
        self.assertTrue(response["success"])
        payload = self.master.list_departments()
        self.assertEqual(len(payload["data"]), 1)
        self.assertEqual(payload["data"][0]["dept_code"], "QA")

    def test_duplicate_department_returns_conflict(self):
        self.master.create_department(self.s.DepartmentCreate(dept_code="QA", dept_name="品質部"))
        with self.assertRaises(HTTPException) as ctx:
            self.master.create_department(self.s.DepartmentCreate(dept_code="QA", dept_name="重複部門"))
        self.assertEqual(ctx.exception.status_code, 409)

    # ── 客戶 GET by ID / PUT ─────────────────────────────────

    def test_get_and_update_customer(self):
        created = self.customers.create_customer(self.s.CustomerCreate(customer_code="C001", customer_name="測試客戶"))["data"]
        fetched = self.customers.get_customer(created["id"])["data"]
        self.assertEqual(fetched["customer_code"], "C001")
        updated = self.customers.update_customer(created["id"], self.s.CustomerUpdate(customer_name="更新客戶", status="inactive"))["data"]
        self.assertEqual(updated["customer_name"], "更新客戶")
        self.assertEqual(updated["status"], "inactive")

    def test_get_customer_not_found(self):
        with self.assertRaises(HTTPException) as ctx:
            self.customers.get_customer("nonexistent-id")
        self.assertEqual(ctx.exception.status_code, 404)

    # ── 供應商 GET by ID / PUT ───────────────────────────────

    def test_get_and_update_supplier(self):
        created = self.suppliers.create_supplier(self.s.SupplierCreate(supplier_code="S001", supplier_name="測試供應商"))["data"]
        fetched = self.suppliers.get_supplier(created["id"])["data"]
        self.assertEqual(fetched["supplier_code"], "S001")
        updated = self.suppliers.update_supplier(created["id"], self.s.SupplierUpdate(category="化工"))["data"]
        self.assertEqual(updated["status"], "active")

    # ── 產品 GET by ID / PUT ─────────────────────────────────

    def test_get_and_update_product(self):
        created = self.products.create_product(self.s.ProductCreate(product_code="P001", product_name="測試產品", spec_summary="ISO spec"))["data"]
        fetched = self.products.get_product(created["id"])["data"]
        self.assertEqual(fetched["spec_summary"], "ISO spec")
        updated = self.products.update_product(created["id"], self.s.ProductUpdate(product_name="更新產品"))["data"]
        self.assertEqual(updated["product_name"], "更新產品")

    # ── 材料主檔 CRUD ────────────────────────────────────────

    def test_material_crud(self):
        created = self.products.create_material(self.s.MaterialMasterCreate(material_code="M001", material_name="IPA 清洗劑", unit="L"))["data"]
        self.assertEqual(created["material_code"], "M001")
        listed = self.products.list_materials()["data"]
        self.assertEqual(len(listed), 1)
        fetched = self.products.get_material(created["id"])["data"]
        self.assertEqual(fetched["unit"], "L")
        updated = self.products.update_material(created["id"], self.s.MaterialMasterUpdate(unit="KG"))["data"]
        self.assertEqual(updated["status"], "active")

    # ── BOM CRUD ─────────────────────────────────────────────

    def test_bom_crud(self):
        product = self.products.create_product(self.s.ProductCreate(product_code="P001", product_name="成品"))["data"]
        material = self.products.create_material(self.s.MaterialMasterCreate(material_code="M001", material_name="原料", unit="L"))["data"]
        added = self.bom.add_bom_item(product["id"], self.s.BomItemCreate(material_id=material["id"], qty_per=2.5))["data"]
        self.assertEqual(float(added["qty_per"]), 2.5)
        bom_list = self.bom.list_bom(product["id"])["data"]
        self.assertEqual(len(bom_list), 1)
        deleted = self.bom.delete_bom_item(product["id"], added["id"])
        self.assertTrue(deleted["success"])

    # ── 班次 CRUD ────────────────────────────────────────────

    def test_shift_crud(self):
        created = self.products.create_shift(self.s.ShiftMasterCreate(shift_code="A", shift_name="早班", start_time="08:00", end_time="17:00"))["data"]
        self.assertEqual(created["shift_code"], "A")
        listed = self.products.list_shifts()["data"]
        self.assertEqual(len(listed), 1)

    # ── 訂單完整流程（含明細、狀態更新）───────────────────────

    def test_sales_order_full_flow(self):
        customer = self.customers.create_customer(self.s.CustomerCreate(customer_code="C001", customer_name="測試客戶"))["data"]
        product = self.products.create_product(self.s.ProductCreate(product_code="P001", product_name="測試產品"))["data"]
        so = self.so.create_sales_order(self.s.SalesOrderCreate(so_no="SO-001", customer_id=customer["id"]))["data"]
        item = self.so.add_sales_order_item(so["id"], self.s.SalesOrderItemCreate(product_id=product["id"], ordered_qty=100))["data"]
        self.assertEqual(float(item["ordered_qty"]), 100)
        detail = self.so.get_sales_order(so["id"])["data"]
        self.assertEqual(len(detail["items"]), 1)
        updated = self.so.update_sales_order_status(so["id"], self.s.StatusUpdate(status="confirmed"))["data"]
        self.assertEqual(updated["order_status"], "confirmed")

    def test_create_sales_order_rejects_missing_customer(self):
        with self.assertRaises(HTTPException) as ctx:
            self.so.create_sales_order(
                self.s.SalesOrderCreate(so_no="SO-404", customer_id="missing-id", order_status="released")
            )
        self.assertEqual(ctx.exception.status_code, 422)

    # ── 工單完整流程 ─────────────────────────────────────────

    def test_work_order_full_flow(self):
        customer = self.customers.create_customer(self.s.CustomerCreate(customer_code="C001", customer_name="測試客戶"))["data"]
        so = self.so.create_sales_order(self.s.SalesOrderCreate(so_no="SO-001", customer_id=customer["id"]))["data"]
        wo = self.wo.create_work_order(self.s.WorkOrderCreate(wo_no="WO-001", so_id=so["id"], planned_qty=100))["data"]
        detail = self.wo.get_work_order(wo["id"])["data"]
        self.assertEqual(float(detail["planned_qty"]), 100)
        self.wo.update_work_order_status(wo["id"], self.s.StatusUpdate(status="in_progress"))
        qty = self.wo.update_work_order_qty(wo["id"], self.s.WorkOrderQtyUpdate(good_qty=95, ng_qty=5))["data"]
        self.assertEqual(float(qty["good_qty"]), 95)
        self.assertEqual(float(qty["ng_qty"]), 5)

    # ── 庫存異動 ─────────────────────────────────────────────

    def test_inventory_transaction(self):
        created = self.inv.create_transaction(self.s.InventoryTransactionCreate(
            trx_no="TRX-001", trx_type="receipt", item_type="material",
            lot_no="LOT-A", qty=50, location_code="WH-01", trx_date=date.today()
        ))["data"]
        self.assertEqual(float(created["qty"]), 50)
        listed = self.inv.list_transactions()["data"]
        self.assertEqual(len(listed), 1)

    # ── 出貨 ─────────────────────────────────────────────────

    def test_shipment_full_flow(self):
        customer = self.customers.create_customer(self.s.CustomerCreate(customer_code="C001", customer_name="測試客戶"))["data"]
        so = self.so.create_sales_order(self.s.SalesOrderCreate(so_no="SO-001", customer_id=customer["id"]))["data"]
        shipment = self.ship.create_shipment(self.s.ShipmentCreate(
            shipment_no="SH-001", so_id=so["id"], shipment_date=date.today()
        ))["data"]
        self.assertEqual(shipment["ship_status"], "draft")
        detail = self.ship.get_shipment(shipment["id"])["data"]
        self.assertEqual(detail["shipment_no"], "SH-001")
        updated = self.ship.update_shipment_status(shipment["id"], self.s.StatusUpdate(status="shipped"))["data"]
        self.assertEqual(updated["ship_status"], "shipped")
        listed = self.ship.list_shipments()["data"]
        self.assertEqual(len(listed), 1)

    # ── Task 3：狀態機守門員驗證 ─────────────────────────────────

    def test_work_order_illegal_transition_is_rejected(self):
        """completed → in_progress 是非法轉換，必須回傳 422。"""
        customer = self.customers.create_customer(self.s.CustomerCreate(customer_code="C001", customer_name="測試客戶"))["data"]
        so = self.so.create_sales_order(self.s.SalesOrderCreate(so_no="SO-001", customer_id=customer["id"]))["data"]
        wo = self.wo.create_work_order(self.s.WorkOrderCreate(
            wo_no="WO-001", so_id=so["id"], planned_qty=10
        ))["data"]
        # draft → in_progress（合法）
        self.wo.update_work_order_status(wo["id"], self.s.StatusUpdate(status="in_progress"))
        # in_progress → completed（合法）
        self.wo.update_work_order_status(wo["id"], self.s.StatusUpdate(status="completed"))
        # completed → in_progress（非法，應拋 422）
        with self.assertRaises(HTTPException) as ctx:
            self.wo.update_work_order_status(wo["id"], self.s.StatusUpdate(status="in_progress"))
        self.assertEqual(ctx.exception.status_code, 422)

    def test_work_order_legal_transition_succeeds(self):
        """draft → in_progress 是合法轉換，必須正常回傳。"""
        customer = self.customers.create_customer(self.s.CustomerCreate(customer_code="C002", customer_name="另一客戶"))["data"]
        so = self.so.create_sales_order(self.s.SalesOrderCreate(so_no="SO-002", customer_id=customer["id"]))["data"]
        wo = self.wo.create_work_order(self.s.WorkOrderCreate(
            wo_no="WO-002", so_id=so["id"], planned_qty=5
        ))["data"]
        updated = self.wo.update_work_order_status(wo["id"], self.s.StatusUpdate(status="in_progress"))
        self.assertTrue(updated["success"])
        self.assertEqual(updated["data"]["wo_status"], "in_progress")

    def test_sales_order_illegal_transition_is_rejected(self):
        """completed → draft 是非法轉換，必須回傳 422。"""
        customer = self.customers.create_customer(self.s.CustomerCreate(customer_code="C003", customer_name="第三客戶"))["data"]
        so = self.so.create_sales_order(self.s.SalesOrderCreate(so_no="SO-003", customer_id=customer["id"]))["data"]
        # draft → confirmed → released → completed
        self.so.update_sales_order_status(so["id"], self.s.StatusUpdate(status="confirmed"))
        self.so.update_sales_order_status(so["id"], self.s.StatusUpdate(status="released"))
        self.so.update_sales_order_status(so["id"], self.s.StatusUpdate(status="completed"))
        # completed → draft（非法）
        with self.assertRaises(HTTPException) as ctx:
            self.so.update_sales_order_status(so["id"], self.s.StatusUpdate(status="draft"))
        self.assertEqual(ctx.exception.status_code, 422)

    def test_shipment_illegal_transition_is_rejected(self):
        """confirmed → draft 是非法轉換，必須回傳 422。"""
        customer = self.customers.create_customer(self.s.CustomerCreate(customer_code="C004", customer_name="第四客戶"))["data"]
        so = self.so.create_sales_order(self.s.SalesOrderCreate(so_no="SO-004", customer_id=customer["id"]))["data"]
        shipment = self.ship.create_shipment(self.s.ShipmentCreate(
            shipment_no="SH-002", so_id=so["id"], shipment_date=date.today()
        ))["data"]
        # draft → shipped → confirmed
        self.ship.update_shipment_status(shipment["id"], self.s.StatusUpdate(status="shipped"))
        self.ship.update_shipment_status(shipment["id"], self.s.StatusUpdate(status="confirmed"))
        # confirmed → draft（非法）
        with self.assertRaises(HTTPException) as ctx:
            self.ship.update_shipment_status(shipment["id"], self.s.StatusUpdate(status="draft"))
        self.assertEqual(ctx.exception.status_code, 422)


if __name__ == "__main__":
    unittest.main()
