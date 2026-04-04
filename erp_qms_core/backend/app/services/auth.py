"""
erp_qms_core/backend/app/services/auth.py
登入 / Token 刷新服務。
"""
from __future__ import annotations

from fastapi import HTTPException, status

from ..core.db import session_scope
from ..core.security import create_token, verify_password
from ..repositories import auth as auth_repo


def login(emp_no: str, password: str) -> dict:
    """
    以員工編號 + 密碼登入，回傳 JWT access token。

    成功回傳：
        {
          "access_token": "<jwt>",
          "token_type": "bearer",
          "user": {"id": ..., "emp_no": ..., "name": ..., "role_code": ...}
        }

    失敗：HTTP 401（不區分「帳號不存在」與「密碼錯誤」，統一訊息防止帳號枚舉）。
    """
    with session_scope() as session:
        user = auth_repo.get_user_by_emp_no(session, emp_no)
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="帳號或密碼錯誤。",
            )
        if not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="帳號或密碼錯誤。",
            )
        role_code = auth_repo.get_role_code(session, user.role_id)
        token = create_token({
            "sub":  user.id,
            "emp":  user.emp_no,
            "name": user.name,
            "role": role_code or "",
        })
        return {
            "access_token": token,
            "token_type":   "bearer",
            "user": {
                "id":        user.id,
                "emp_no":    user.emp_no,
                "name":      user.name,
                "role_code": role_code or "",
            },
        }
