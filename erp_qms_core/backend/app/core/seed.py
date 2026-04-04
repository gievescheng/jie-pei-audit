"""
erp_qms_core/backend/app/core/seed.py
開發環境種子資料：初始角色 + admin 帳號。

正式環境：不執行此腳本；改由管理員手動建立帳號或透過管理 API。
"""
from __future__ import annotations

import os

from .db import session_scope
from .security import hash_password
from ..models.master import Role, User


SEED_ROLES = [
    {"id": "role-admin-000", "role_code": "admin", "role_name": "系統管理員"},
    {"id": "role-qm-000",    "role_code": "qm",    "role_name": "品保/品管人員"},
    {"id": "role-prod-000",  "role_code": "prod",  "role_name": "生產主管"},
    {"id": "role-mgmt-000",  "role_code": "mgmt",  "role_name": "高階主管"},
]

SEED_ADMIN = {
    "id":        "user-admin-000",
    "emp_no":    "ADMIN",
    "name":      "系統管理員",
    "role_id":   "role-admin-000",
    "is_active": True,
}


def seed_dev() -> None:
    """
    在資料庫中建立初始角色和 admin 帳號（若尚未存在）。
    只在開發環境（JEPE_ENV != "production"）執行。
    """
    if os.getenv("JEPE_ENV") == "production":
        return

    admin_password = os.getenv("SEED_ADMIN_PASSWORD", "admin1234")

    with session_scope() as session:
        for r in SEED_ROLES:
            if not session.get(Role, r["id"]):
                session.add(Role(**r))

        if not session.get(User, SEED_ADMIN["id"]):
            data = dict(SEED_ADMIN)
            data["password_hash"] = hash_password(admin_password)
            session.add(User(**data))
