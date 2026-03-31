from __future__ import annotations

from sqlalchemy.exc import IntegrityError

from ..core.db import session_scope
from ..core.errors import integrity_http_error
from ..core.responses import ok
from ..models.master import Department, Role
from ..schemas.master import DepartmentCreate, RoleCreate


def list_departments() -> dict:
    with session_scope() as session:
        rows = session.query(Department).order_by(Department.dept_code.asc()).all()
        return ok([{"id": r.id, "dept_code": r.dept_code, "dept_name": r.dept_name} for r in rows])


def create_department(payload: DepartmentCreate) -> dict:
    try:
        with session_scope() as session:
            row = Department(dept_code=payload.dept_code, dept_name=payload.dept_name)
            session.add(row)
            session.flush()
            return ok({"id": row.id, "dept_code": row.dept_code, "dept_name": row.dept_name}, message="created")
    except IntegrityError as exc:
        raise integrity_http_error(exc) from exc


def list_roles() -> dict:
    with session_scope() as session:
        rows = session.query(Role).order_by(Role.role_code.asc()).all()
        return ok([{"id": r.id, "role_code": r.role_code, "role_name": r.role_name} for r in rows])


def create_role(payload: RoleCreate) -> dict:
    try:
        with session_scope() as session:
            row = Role(role_code=payload.role_code, role_name=payload.role_name, description=payload.description)
            session.add(row)
            session.flush()
            return ok({"id": row.id, "role_code": row.role_code, "role_name": row.role_name}, message="created")
    except IntegrityError as exc:
        raise integrity_http_error(exc) from exc
