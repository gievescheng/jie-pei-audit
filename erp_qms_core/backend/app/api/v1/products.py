from __future__ import annotations

from fastapi import APIRouter, Depends

from ...core.security import require_roles
from ...schemas.master import DepartmentCreate, MaterialMasterCreate, MaterialMasterUpdate, RoleCreate, ShiftMasterCreate
from ...schemas.products import ProductCreate, ProductUpdate
from ...services import master as master_svc
from ...services import products as svc

router = APIRouter()


@router.get("/master/departments", dependencies=[Depends(require_roles())])
def list_departments():
    return master_svc.list_departments()


@router.post("/master/departments", status_code=201, dependencies=[Depends(require_roles("admin", "qm"))])
def create_department(payload: DepartmentCreate):
    return master_svc.create_department(payload)


@router.get("/master/roles", dependencies=[Depends(require_roles())])
def list_roles():
    return master_svc.list_roles()


@router.post("/master/roles", status_code=201, dependencies=[Depends(require_roles("admin"))])
def create_role(payload: RoleCreate):
    return master_svc.create_role(payload)


@router.get("/master/products", dependencies=[Depends(require_roles())])
def list_products():
    return svc.list_products()


@router.post("/master/products", status_code=201, dependencies=[Depends(require_roles("admin", "qm"))])
def create_product(payload: ProductCreate):
    return svc.create_product(payload)


@router.get("/master/products/{product_id}", dependencies=[Depends(require_roles())])
def get_product(product_id: str):
    return svc.get_product(product_id)


@router.put("/master/products/{product_id}", dependencies=[Depends(require_roles("admin", "qm"))])
def update_product(product_id: str, payload: ProductUpdate):
    return svc.update_product(product_id, payload)


@router.get("/master/materials", dependencies=[Depends(require_roles())])
def list_materials():
    return svc.list_materials()


@router.post("/master/materials", status_code=201, dependencies=[Depends(require_roles("admin", "qm"))])
def create_material(payload: MaterialMasterCreate):
    return svc.create_material(payload)


@router.get("/master/materials/{material_id}", dependencies=[Depends(require_roles())])
def get_material(material_id: str):
    return svc.get_material(material_id)


@router.put("/master/materials/{material_id}", dependencies=[Depends(require_roles("admin", "qm"))])
def update_material(material_id: str, payload: MaterialMasterUpdate):
    return svc.update_material(material_id, payload)


@router.get("/master/shifts", dependencies=[Depends(require_roles())])
def list_shifts():
    return svc.list_shifts()


@router.post("/master/shifts", status_code=201, dependencies=[Depends(require_roles("admin", "qm"))])
def create_shift(payload: ShiftMasterCreate):
    return svc.create_shift(payload)
