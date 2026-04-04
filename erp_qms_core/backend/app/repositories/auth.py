"""
erp_qms_core/backend/app/repositories/auth.py
使用者查詢（供 auth service 使用）。
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from ..models.master import Role, User


def get_user_by_emp_no(session: Session, emp_no: str) -> User | None:
    return session.query(User).filter(
        User.emp_no == emp_no,
    ).first()


def get_role_code(session: Session, role_id: str | None) -> str | None:
    if not role_id:
        return None
    role = session.get(Role, role_id)
    return role.role_code if role else None
