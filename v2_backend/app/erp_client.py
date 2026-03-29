"""
erp_client.py — QMS 系統向 ERP 核心系統讀取主資料的 HTTP 客戶端

說明：
- 透過 /api/internal/ 端點讀取 ERP 資料（產品、客戶、供應商、工單）
- 使用服務金鑰（X-Service-Key）進行服務間身份驗證，不需要使用者登入
- 若 ERP 服務暫時無法連線，回傳空清單並記錄警告（不影響 QMS 主要功能）
"""
from __future__ import annotations

import logging

import httpx

from .config import settings

logger = logging.getLogger(__name__)

_HEADERS = {"X-Service-Key": settings.erp_service_key}


def _get(path: str, params: dict | None = None) -> dict:
    """向 ERP 發送 GET 請求，失敗時回傳空的 items 清單。"""
    url = f"{settings.erp_base_url}{path}"
    try:
        with httpx.Client(timeout=settings.erp_timeout) as client:
            resp = client.get(url, headers=_HEADERS, params=params or {})
            resp.raise_for_status()
            body = resp.json()
            return body.get("data", {})
    except httpx.HTTPStatusError as exc:
        logger.warning("ERP API 回傳錯誤 %s %s: %s", exc.response.status_code, url, exc.response.text[:200])
        return {"items": []}
    except Exception as exc:
        logger.warning("ERP API 無法連線 %s: %s", url, exc)
        return {"items": []}


def list_products(q: str = "", limit: int = 200) -> list[dict]:
    """取得產品清單。"""
    data = _get("/api/internal/products", {"q": q, "limit": limit})
    return data.get("items", [])


def list_customers(q: str = "", limit: int = 200) -> list[dict]:
    """取得客戶清單。"""
    data = _get("/api/internal/customers", {"q": q, "limit": limit})
    return data.get("items", [])


def list_suppliers(q: str = "", limit: int = 200) -> list[dict]:
    """取得供應商清單。"""
    data = _get("/api/internal/suppliers", {"q": q, "limit": limit})
    return data.get("items", [])


def list_work_orders(q: str = "", limit: int = 200) -> list[dict]:
    """取得工單清單。"""
    data = _get("/api/internal/work-orders", {"q": q, "limit": limit})
    return data.get("items", [])
