from __future__ import annotations

import json
import shutil
import tempfile
import zipfile
from datetime import date, datetime
from pathlib import Path

from openpyxl import load_workbook

import generate_record
import shipment_draft

BASE_DIR = Path(__file__).parent.resolve()


def _tmp_path(suffix: str) -> Path:
    handle = tempfile.NamedTemporaryFile(suffix=suffix, delete=False, dir=tempfile.gettempdir())
    handle.close()
    return Path(handle.name)


def _normalize_text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_date(value) -> str:
    if not value:
        return ""
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = _normalize_text(value).replace("/", "-")
    if " " in text:
        text = text.split(" ", 1)[0]
    return text


def _display_date(value) -> str:
    iso = _normalize_date(value)
    return iso.replace("-", "/") if iso else ""


def _parse_int(value):
    text = _normalize_text(value).replace(",", "")
    if not text:
        return None
    try:
        return int(float(text))
    except Exception:
        return None


def _find_template(prefix: str) -> Path:
    candidates = [
        path
        for path in BASE_DIR.rglob(f"{prefix}*.xlsx")
        if path.parent.name == "表單"
    ]
    if not candidates:
        raise FileNotFoundError(f"Template not found for prefix: {prefix}")
    return sorted(candidates, key=lambda item: (len(item.parts), len(str(item))))[0]


CATALOG = [
    {
        "code": "env_record",
        "title": "6.1 環境監控記錄表",
        "description": "用環境監測資料產出正式環境監控記錄。",
        "requires": ["env_records"],
        "bundle": False,
    },
    {
        "code": "production_daily",
        "title": "11.5 生產日報表",
        "description": "用生產批次資料產出生產日報。",
        "requires": ["prod_records"],
        "bundle": False,
    },
    {
        "code": "quality_incoming",
        "title": "12.1 品質管理記錄表(原料)",
        "description": "用進料檢驗資料產出原料品質記錄。",
        "requires": ["quality_records"],
        "bundle": False,
    },
    {
        "code": "material_request_112",
        "title": "11.2 領料單",
        "description": "用訂單與出貨/備料資料產生領料單草稿。",
        "requires": ["shipment"],
        "bundle": False,
    },
    {
        "code": "shipment_order_143",
        "title": "14.3 出貨單",
        "description": "用訂單、批號與數量資料產生出貨單草稿。",
        "requires": ["shipment"],
        "bundle": False,
    },
    {
        "code": "shipping_inspection_125",
        "title": "12.5 出貨檢查紀錄表",
        "description": "產出出貨檢查執行紀錄草稿。",
        "requires": ["shipment"],
        "bundle": False,
    },
    {
        "code": "shipping_check_145",
        "title": "14.5 出貨檢查表",
        "description": "產出包裝/標示出貨檢查草稿。",
        "requires": ["shipment"],
        "bundle": False,
    },
    {
        "code": "shipping_pack",
        "title": "出貨流程紀錄包",
        "description": "一次產出出貨單、出貨檢查紀錄與出貨檢查表。",
        "requires": ["shipment"],
        "bundle": True,
    },
    {
        "code": "cip_152",
        "title": "15.2 製程缺陷追蹤改善(CIP)紀錄表",
        "description": "用不符合資料帶出改善追蹤表草稿。",
        "requires": ["nonconformance"],
        "bundle": False,
    },
]


KEYWORDS = {
    "shipping_pack": ["出貨流程", "出貨程序", "出貨檢查", "出貨單", "出貨"],
    "shipment_order_143": ["出貨單", "出貨"],
    "shipping_inspection_125": ["出貨檢查紀錄", "出貨檢查", "包裝", "檢查紀錄"],
    "shipping_check_145": ["標示", "包裝", "檢查表", "出貨檢查"],
    "material_request_112": ["領料", "備料", "投料"],
    "cip_152": ["不符合", "缺陷", "改善", "cip", "矯正", "再發", "追蹤"],
    "production_daily": ["生產", "日報", "良率", "投入", "產出"],
    "quality_incoming": ["進料", "原料", "品質檢驗", "來料"],
    "env_record": ["環境", "溫濕度", "粒子", "壓差", "監控"],
}


def get_catalog() -> list[dict]:
    return [dict(item) for item in CATALOG]


def suggest_templates(prompt: str, context: dict | None = None) -> list[dict]:
    prompt_text = _normalize_text(prompt).lower()
    context = context or {}
    availability = {
        "env_records": int(context.get("env_count") or 0) > 0,
        "prod_records": int(context.get("prod_count") or 0) > 0,
        "quality_records": int(context.get("quality_count") or 0) > 0,
        "shipment": int(context.get("shipment_order_count") or 0) > 0,
        "nonconformance": int(context.get("nonconformance_count") or 0) > 0,
    }
    scored = []
    for item in get_catalog():
        score = 0
        for token in KEYWORDS.get(item["code"], []):
            if token.lower() in prompt_text:
                score += 3 if token in prompt else 2
        if all(availability.get(req, False) for req in item["requires"]):
            score += 1
        scored.append({
            **item,
            "score": score,
            "available": all(availability.get(req, False) for req in item["requires"]),
        })
    scored.sort(key=lambda item: (-item["score"], not item["available"], item["title"]))
    return scored


def _get_shipment_defaults(payload: dict) -> dict:
    body = payload.get("shipment_request") or {}
    order_no = _normalize_text(body.get("order_no"))
    if not order_no:
        raise ValueError("出貨相關模板需要 order_no。")
    catalog_map = {item["order_no"]: item for item in shipment_draft.get_order_catalog()}
    defaults = catalog_map.get(order_no, {"order_no": order_no})
    selected_lots = body.get("selected_lots") or []
    if not isinstance(selected_lots, list):
        selected_lots = []
    return {
        "order_no": order_no,
        "date": _normalize_date(body.get("date")) or defaults.get("ship_date_suggested") or date.today().isoformat(),
        "department": _normalize_text(body.get("department")) or defaults.get("department_suggested") or "資材課",
        "requester": _normalize_text(body.get("requester")) or defaults.get("requester_suggested") or "",
        "product_name": _normalize_text(body.get("product_name")) or defaults.get("product_name_suggested") or defaults.get("source_product") or "",
        "spec": _normalize_text(body.get("spec")) or defaults.get("spec_suggested") or "",
        "quantity": _parse_int(body.get("quantity")) or _parse_int(defaults.get("quantity_suggested")) or "",
        "unit": _normalize_text(body.get("unit")) or defaults.get("unit_suggested") or "片",
        "remark": _normalize_text(body.get("remark")) or defaults.get("remark_suggested") or "",
        "batch_display": _normalize_text(body.get("batch_display")) or defaults.get("batch_display_suggested") or order_no,
        "selected_lots": selected_lots,
    }


def _build_material_request(payload: dict) -> tuple[Path, str, str]:
    data = _get_shipment_defaults(payload)
    template = _find_template("11.2")
    out_path = _tmp_path(".xlsx")
    shutil.copy2(template, out_path)
    wb = load_workbook(out_path)
    ws = wb.active
    ws["B3"] = data["department"]
    ws["D3"] = data["requester"]
    ws["F3"] = _display_date(data["date"])
    ws["A5"] = 1
    ws["B5"] = data["batch_display"]
    ws["C5"] = data["product_name"]
    ws["D5"] = data["spec"]
    ws["E5"] = data["quantity"]
    ws["F5"] = data["unit"]
    ws["G5"] = data["remark"]
    wb.save(out_path)
    return out_path, f"{data['order_no']}_領料單.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _build_shipping_inspection_125(payload: dict) -> tuple[Path, str, str]:
    data = _get_shipment_defaults(payload)
    template = _find_template("12.5")
    out_path = _tmp_path(".xlsx")
    shutil.copy2(template, out_path)
    wb = load_workbook(out_path)
    ws = wb.active
    year_text = data["date"][:4] if data["date"] else str(date.today().year)
    ws["B2"] = year_text
    ws["D2"] = "成品包裝/出貨"
    ws["B3"] = data["department"]
    ws["D3"] = data["requester"]
    ws["F3"] = _display_date(data["date"])
    checks = [
        "出貨單資訊確認",
        "產品標示確認",
        "包裝外觀確認",
        "隨附文件確認",
    ]
    for index, title in enumerate(checks, start=6):
        ws[f"A{index}"] = _display_date(data["date"])
        ws[f"B{index}"] = title
        ws[f"C{index}"] = data["requester"]
        ws[f"D{index}"] = "OK"
        ws[f"E{index}"] = data["requester"]
        ws[f"F{index}"] = ""
        ws[f"G{index}"] = f"訂單 {data['order_no']} / {data['batch_display']}"
    wb.save(out_path)
    return out_path, f"{data['order_no']}_出貨檢查紀錄表.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _build_shipping_check_145(payload: dict) -> tuple[Path, str, str]:
    data = _get_shipment_defaults(payload)
    template = _find_template("14.5")
    out_path = _tmp_path(".xlsx")
    shutil.copy2(template, out_path)
    wb = load_workbook(out_path)
    ws = wb.active
    ws["B4"] = _display_date(data["date"])
    ws["D4"] = data["batch_display"]
    ws["G4"] = data["order_no"]
    ws["J4"] = data["product_name"]
    ws["L4"] = data["quantity"]
    for row in range(7, 12):
        ws[f"B{row}"] = _display_date(data["date"])
        ws[f"E{row}"] = data["quantity"]
        ws[f"F{row}"] = "OK"
        ws[f"I{row}"] = data["remark"]
    wb.save(out_path)
    return out_path, f"{data['order_no']}_出貨檢查表.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _build_cip_tracker(payload: dict) -> tuple[Path, str, str]:
    nonconformance = payload.get("nonconformance") or {}
    if not nonconformance:
        raise ValueError("CIP 模板需要一筆不符合資料。")
    template = _find_template("15.2")
    out_path = _tmp_path(".xlsx")
    shutil.copy2(template, out_path)
    wb = load_workbook(out_path)
    ws = wb.active
    status_map = {
        "已關閉": "Closed",
        "進行中": "In progress",
        "待處理": "Open",
        "逾期": "Open",
    }
    issue_title = _normalize_text(nonconformance.get("type")) or "不符合改善追蹤"
    description = _normalize_text(nonconformance.get("description"))
    dept = _normalize_text(nonconformance.get("dept"))
    issue_date = _display_date(nonconformance.get("date"))
    ws["A3"] = issue_title
    ws["B3"] = f"{description}（部門：{dept}；日期：{issue_date}）"
    ws["C3"] = _normalize_text(nonconformance.get("rootCause")) or "待補根本原因分析"
    ws["D3"] = "先進行圍堵處置，避免同類問題持續流出。"
    ws["E3"] = _normalize_text(nonconformance.get("correctiveAction")) or "待補矯正措施"
    ws["F3"] = _normalize_text(nonconformance.get("effectiveness")) or "完成後追蹤 30 天內是否再發"
    ws["G3"] = "確認改善措施完成，並追蹤同類缺陷是否再發。"
    ws["H3"] = _normalize_text(nonconformance.get("closeDate")) or "待補佐證"
    ws["I3"] = _normalize_text(nonconformance.get("responsible")) or "待指派"
    ws["J3"] = _display_date(nonconformance.get("dueDate"))
    ws["K3"] = status_map.get(_normalize_text(nonconformance.get("status")), "Open")
    wb.save(out_path)
    record_id = _normalize_text(nonconformance.get("id")) or "CIP"
    return out_path, f"{record_id}_CIP紀錄表.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _build_shipment_pack(payload: dict) -> tuple[Path, str, str]:
    shipment_payload = payload.get("shipment_request") or {}
    generated = []
    ship_path, ship_name = shipment_draft.build_shipment_draft(shipment_payload)
    generated.append((Path(ship_path), ship_name))
    for builder in (_build_shipping_inspection_125, _build_shipping_check_145):
        path, name, _ = builder(payload)
        generated.append((path, name))

    order_no = _normalize_text(shipment_payload.get("order_no")) or "shipment"
    out_path = _tmp_path(".zip")
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path, name in generated:
            archive.write(file_path, arcname=name)
    return out_path, f"{order_no}_出貨流程紀錄包.zip", "application/zip"


def generate_template(payload: dict) -> tuple[Path, str, str]:
    template_code = _normalize_text(payload.get("template_code"))
    if not template_code:
        raise ValueError("template_code is required.")

    if template_code == "env_record":
        out_path = _tmp_path(".xlsx")
        return Path(generate_record.run("env", payload.get("env_records") or [], str(out_path))), "環境監控記錄.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    if template_code == "production_daily":
        out_path = _tmp_path(".xlsx")
        return Path(generate_record.run("production", payload.get("prod_records") or [], str(out_path))), "生產日報表.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    if template_code == "quality_incoming":
        out_path = _tmp_path(".xlsx")
        return Path(generate_record.run("quality", payload.get("quality_records") or [], str(out_path))), "品質管理記錄表(原料).xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    if template_code == "shipment_order_143":
        body = payload.get("shipment_request") or {}
        out_path, download_name = shipment_draft.build_shipment_draft(body)
        return Path(out_path), download_name, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    if template_code == "material_request_112":
        return _build_material_request(payload)
    if template_code == "shipping_inspection_125":
        return _build_shipping_inspection_125(payload)
    if template_code == "shipping_check_145":
        return _build_shipping_check_145(payload)
    if template_code == "shipping_pack":
        return _build_shipment_pack(payload)
    if template_code == "cip_152":
        return _build_cip_tracker(payload)
    raise ValueError(f"Unsupported template_code: {template_code}")


def build_engine_payload_snapshot(payload: dict) -> str:
    snapshot = {
        "template_code": payload.get("template_code"),
        "prompt": payload.get("prompt"),
        "shipment_request": payload.get("shipment_request"),
        "nonconformance": payload.get("nonconformance"),
        "counts": {
            "env": len(payload.get("env_records") or []),
            "production": len(payload.get("prod_records") or []),
            "quality": len(payload.get("quality_records") or []),
        },
    }
    return json.dumps(snapshot, ensure_ascii=False)
