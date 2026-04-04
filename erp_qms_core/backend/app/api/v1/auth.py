"""
erp_qms_core/backend/app/api/v1/auth.py
POST /api/auth/login
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from ...services import auth as auth_svc

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    emp_no: str
    password: str


@router.post("/login")
def login(body: LoginRequest) -> dict:
    """
    登入並取得 JWT。

    Request body:
        { "emp_no": "A001", "password": "your-password" }

    Response (200):
        {
          "access_token": "eyJ...",
          "token_type": "bearer",
          "user": { "id": "...", "emp_no": "A001", "name": "陳...", "role_code": "qm" }
        }

    Error (401):
        { "detail": "帳號或密碼錯誤。" }
    """
    return auth_svc.login(body.emp_no, body.password)
