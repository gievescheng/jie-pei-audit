"""
seed_admin.py — 建立初始管理員角色與帳號

執行方式（在 erp_qms_core/backend 目錄下）：
    python seed_admin.py

注意事項：
- 此腳本可重複執行，不會產生重複資料（幂等）
- 執行完請立即修改預設密碼！
"""
from __future__ import annotations

import sys
import os

# 讓 Python 找得到 app 模組
sys.path.insert(0, os.path.dirname(__file__))

from app.auth import hash_password
from app.db import session_scope
from app import models

# ── 初始設定 ────────────────────────────────────────────
ADMIN_ROLE_CODE = "ADMIN"
ADMIN_EMP_NO = "EMP001"
ADMIN_NAME = "系統管理員"
ADMIN_EMAIL = "admin@local"
ADMIN_PASSWORD = "Admin1234!"   # ← 登入後請立即修改！

# 系統支援的所有權限代碼
ALL_PERMISSIONS = [
    ("master.department.read",   "查詢部門"),
    ("master.department.write",  "新增/修改部門"),
    ("master.role.read",         "查詢角色"),
    ("master.role.write",        "新增/修改角色"),
    ("master.customer.read",     "查詢客戶"),
    ("master.customer.write",    "新增/修改客戶"),
    ("master.supplier.read",     "查詢供應商"),
    ("master.supplier.write",    "新增/修改供應商"),
    ("master.product.read",      "查詢產品"),
    ("master.product.write",     "新增/修改產品"),
    ("inventory.location.read",  "查詢庫存位置"),
    ("inventory.location.write", "新增/修改庫存位置"),
    ("order.sales.read",         "查詢銷售訂單"),
    ("order.sales.write",        "新增/修改銷售訂單"),
    ("order.work.read",          "查詢工單"),
    ("order.work.write",         "新增/修改工單"),
    ("auth.user.read",           "查詢使用者"),
    ("auth.user.write",          "新增/修改使用者"),
]


def main():
    print("=" * 50)
    print("ERP-QMS 核心系統 — 初始資料建立")
    print("=" * 50)

    with session_scope() as session:
        # 1. 建立管理員角色
        role = session.query(models.Role).filter_by(role_code=ADMIN_ROLE_CODE).first()
        if role is None:
            role = models.Role(
                role_code=ADMIN_ROLE_CODE,
                role_name="系統管理員",
                description="擁有系統所有功能的完整存取權限",
            )
            session.add(role)
            session.flush()
            print(f"[OK] 已建立角色：{ADMIN_ROLE_CODE}（{role.id}）")
        else:
            print(f"  角色 {ADMIN_ROLE_CODE} 已存在，略過")

        # 2. 建立所有權限（若不存在則新增）
        existing_codes = {
            p.permission_code
            for p in session.query(models.RolePermission)
                             .filter_by(role_id=role.id).all()
        }
        added = 0
        for code, name in ALL_PERMISSIONS:
            if code not in existing_codes:
                session.add(models.RolePermission(
                    role_id=role.id,
                    permission_code=code,
                    permission_name=name,
                ))
                added += 1
        session.flush()
        print(f"[OK] 已設定 {len(ALL_PERMISSIONS)} 項權限（本次新增 {added} 項）")

        # 3. 建立管理員帳號
        user = session.query(models.User).filter_by(emp_no=ADMIN_EMP_NO).first()
        if user is None:
            user = models.User(
                emp_no=ADMIN_EMP_NO,
                name=ADMIN_NAME,
                email=ADMIN_EMAIL,
                password_hash=hash_password(ADMIN_PASSWORD),
                role_id=role.id,
                is_active=True,
            )
            session.add(user)
            session.flush()
            print(f"[OK] 已建立管理員帳號：{ADMIN_EMP_NO}")
            print()
            print("  ┌─────────────────────────────┐")
            print(f"  │  員工編號：{ADMIN_EMP_NO:<18} │")
            print(f"  │  預設密碼：{ADMIN_PASSWORD:<18} │")
            print("  └─────────────────────────────┘")
            print()
            print("  [!!] 請登入後立即修改密碼！")
        else:
            print(f"  帳號 {ADMIN_EMP_NO} 已存在，略過")

    print()
    print("初始資料建立完成！")
    print("現在可以使用以下 API 登入：")
    print("  POST http://127.0.0.1:8895/api/auth/login")


if __name__ == "__main__":
    main()
