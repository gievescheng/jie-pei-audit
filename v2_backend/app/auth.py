"""
v2_backend/app/auth.py
最輕量的 API Key 驗證 dependency。
正式 JWT/RBAC 上線後，此模組可直接替換。
"""
from __future__ import annotations

import logging
import os

from fastapi import Header, HTTPException

from .config import settings

logger = logging.getLogger(__name__)
_auth_warning_logged = False


def require_api_key(x_api_key: str = Header(default="")) -> None:
    """
    若環境變數 INTERNAL_API_KEY 有設定，則要求 Header 中的 X-Api-Key 匹配。
    若 INTERNAL_API_KEY 未設定（空字串），則跳過驗證（開發模式）。
    生產環境（DATABASE_URL 含 postgresql）未設定 key 時發出警告。
    """
    global _auth_warning_logged
    if not settings.internal_api_key:
        if not _auth_warning_logged:
            db_url = os.getenv("DATABASE_URL", "")
            if "postgresql" in db_url.lower():
                logger.warning(
                    "⚠ INTERNAL_API_KEY 未設定！生產環境的所有 API 端點均無認證保護。"
                    "請設定環境變數 INTERNAL_API_KEY 以啟用認證。"
                )
            _auth_warning_logged = True
        return  # 開發模式：不驗證
    if x_api_key != settings.internal_api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")
