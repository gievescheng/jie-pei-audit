# AGENT_TASKS_JWT_RBAC.md
# jie-pei-audit — JWT / RBAC 主線任務
# 適用：Claude Code / Codex
#
# 前置條件：AGENT_TASKS.md 的 Task 1–6 已全部完成並推送。
# 本文件接續上一輪，讓系統從「無認證的內部工具」升級為「正式多人系統」。

---

## 快速定位

```
repo:          https://github.com/gievescheng/jie-pei-audit
關鍵現有檔案:
  erp_qms_core/backend/app/core/security.py     ← JWT 骨架已存在（待接通）
  erp_qms_core/backend/app/models/master.py     ← User / Role / RolePermission 已定義
  erp_qms_core/backend/app/core/config.py       ← 待加入 JWT_SECRET、TOKEN_EXPIRE_MINUTES
  erp_qms_core/backend/app/api/v1/router.py     ← 待加入 /auth 路由
  erp_qms_core/backend/requirements.txt         ← 待加入 PyJWT、bcrypt
  erp_qms_core/backend/tests/integration/test_core_smoke.py  ← 現有整合測試模式參考
```

## 現有狀態確認（執行前請先核對）

- `security.py` 已有 `create_token()`、`decode_token()`、`require_roles()` 骨架，
  但 `hash_password()` 目前仍是 **SHA-256**（MVP 等級），需升級為 bcrypt。
- `User` model 有 `emp_no`、`password_hash`、`role_id`、`is_active` 欄位。
- `Role` / `RolePermission` model 已存在。
- `config.py` 目前沒有 `jwt_secret` 和 `token_expire_minutes` 屬性。
- `requirements.txt` 目前沒有 `PyJWT` 和 `bcrypt`。

---

## 絕對禁止事項

- **禁止** 修改任何 QMS 歸檔文件資料夾（`0 品質手冊/` 等）
- **禁止** 更改 PK 型別（UUID Text 不可改為 Integer）
- **禁止** 兩個 Alembic 歷史互相干擾（只改 `erp_qms_core/backend/alembic.ini`）
- **禁止** 引入 microservices 或替換 FastAPI / SQLAlchemy
- **禁止** 一次大改 `audit-dashboard.jsx`；本輪任務不涉及前端，不要動 `frontend_src/`

---

## Task A：升級密碼雜湊 + 補齊 config

**狀態：** [ ] 待執行

### A-1：requirements.txt 補套件

在 `erp_qms_core/backend/requirements.txt` 加入：

```
PyJWT>=2.8.0
bcrypt>=4.1.0
```

同步在 `erp_qms_core/backend/requirements-dev.txt` 確認 `-r requirements.txt` 存在
（通常已有，確認即可，不需重複加）。

### A-2：config.py 加入 JWT 設定

在現有 `_Settings` class 加入兩個屬性：

```python
@property
def jwt_secret(self) -> str:
    secret = os.getenv("ERP_QMS_CORE_JWT_SECRET", "")
    if not secret:
        raise RuntimeError(
            "ERP_QMS_CORE_JWT_SECRET 未設定。"
            " 請在 .env 或環境變數中設定一個隨機字串（至少 32 字元）。"
        )
    return secret

@property
def token_expire_minutes(self) -> int:
    return int(os.getenv("ERP_QMS_CORE_TOKEN_EXPIRE_MINUTES", "480"))  # 預設 8 小時
```

### A-3：security.py 升級 bcrypt + 接通 config

將整個 `security.py` 改寫為以下版本（保留所有現有函式簽名，升級實作）：

```python
"""
erp_qms_core/backend/app/core/security.py
密碼雜湊、JWT 簽發 / 驗證、FastAPI RBAC 依賴。
"""
from __future__ import annotations

import datetime
from typing import Callable

import bcrypt
import jwt as pyjwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings


# ── 密碼雜湊（bcrypt）─────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    """bcrypt 雜湊，rounds=12，自動加鹽。"""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """安全比對密碼（常數時間，防 timing attack）。"""
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


# ── JWT 簽發 / 解碼 ───────────────────────────────────────────────────────────

def create_token(payload: dict) -> str:
    """
    簽發 JWT。payload 中的 exp 若未指定，自動加入過期時間。
    呼叫端應在 payload 中提供：
      sub  : str   — user id（UUID）
      role : str   — role_code
      name : str   — 顯示名稱（可選）
    """
    data = dict(payload)
    if "exp" not in data:
        data["exp"] = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            minutes=settings.token_expire_minutes
        )
    return pyjwt.encode(data, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> dict | None:
    """
    驗證並解碼 JWT。
    回傳 payload dict；若 token 無效或過期，回傳 None。
    """
    try:
        return pyjwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except pyjwt.ExpiredSignatureError:
        return None
    except pyjwt.InvalidTokenError:
        return None


# ── FastAPI 依賴：RBAC 守門員 ─────────────────────────────────────────────────

_bearer = HTTPBearer(auto_error=False)


def require_roles(*allowed_roles: str) -> Callable:
    """
    FastAPI 依賴工廠，限制只有指定角色可存取路由。

    使用方式：
        @router.get("/admin", dependencies=[Depends(require_roles("admin", "qm"))])

    若 allowed_roles 為空，只驗證登入狀態，不限角色。
    """
    def _check(
        credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    ) -> dict:
        if credentials is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="需要登入才能存取此資源。",
                headers={"WWW-Authenticate": "Bearer"},
            )
        payload = decode_token(credentials.credentials)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token 無效或已過期，請重新登入。",
                headers={"WWW-Authenticate": "Bearer"},
            )
        role = payload.get("role", "")
        if allowed_roles and role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"權限不足。此操作需要角色：{', '.join(allowed_roles)}。",
            )
        return payload
    return _check
```

### A-4：新增 unit test

在 `erp_qms_core/backend/tests/unit/test_core.py` 補充（加到現有 class 後面）：

```python
class TestPasswordHash(unittest.TestCase):
    """bcrypt 雜湊行為驗證。"""

    def test_hash_and_verify_correct_password(self):
        from erp_qms_core.backend.app.core.security import hash_password, verify_password
        hashed = hash_password("correct-password")
        self.assertTrue(verify_password("correct-password", hashed))

    def test_wrong_password_fails(self):
        from erp_qms_core.backend.app.core.security import hash_password, verify_password
        hashed = hash_password("correct-password")
        self.assertFalse(verify_password("wrong-password", hashed))

    def test_empty_password_handled_safely(self):
        from erp_qms_core.backend.app.core.security import hash_password, verify_password
        hashed = hash_password("")
        self.assertTrue(verify_password("", hashed))
        self.assertFalse(verify_password("not-empty", hashed))

    def test_two_hashes_of_same_password_differ(self):
        """bcrypt 每次加鹽不同，兩次雜湊結果不應相同。"""
        from erp_qms_core.backend.app.core.security import hash_password
        h1 = hash_password("same-password")
        h2 = hash_password("same-password")
        self.assertNotEqual(h1, h2)


class TestJWT(unittest.TestCase):
    """JWT 簽發與驗證。測試前需設定 ERP_QMS_CORE_JWT_SECRET。"""

    def setUp(self):
        import os
        os.environ["ERP_QMS_CORE_JWT_SECRET"] = "test-secret-for-unit-test-only"

    def test_create_and_decode_token(self):
        from erp_qms_core.backend.app.core.security import create_token, decode_token
        payload = {"sub": "user-uuid-001", "role": "qm", "name": "測試使用者"}
        token = create_token(payload)
        decoded = decode_token(token)
        self.assertIsNotNone(decoded)
        self.assertEqual(decoded["sub"], "user-uuid-001")
        self.assertEqual(decoded["role"], "qm")

    def test_invalid_token_returns_none(self):
        from erp_qms_core.backend.app.core.security import decode_token
        self.assertIsNone(decode_token("not-a-valid-token"))
        self.assertIsNone(decode_token(""))

    def test_expired_token_returns_none(self):
        import datetime
        from erp_qms_core.backend.app.core.security import create_token, decode_token
        payload = {
            "sub": "user-uuid-002",
            "role": "qm",
            "exp": datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=1),
        }
        token = create_token(payload)
        self.assertIsNone(decode_token(token))
```

### 完成標準

```bash
cd erp_qms_core/backend
pip install -r requirements-dev.txt
python -m pytest tests/unit/test_core.py -v
# 預期：TestPasswordHash 4 cases + TestJWT 3 cases 全通過
```

### 結果記錄

```
# AI Agent 填寫：
bcrypt 測試通過數：
JWT 測試通過數：
```

---

## Task B：Auth 服務層 + Login API

**狀態：** [ ] 待執行

### B-1：新建 `erp_qms_core/backend/app/services/auth.py`

```python
"""
erp_qms_core/backend/app/services/auth.py
登入 / Token 刷新服務。
"""
from __future__ import annotations

from fastapi import HTTPException, status

from ..core.db import session_scope
from ..core.security import create_token, hash_password, verify_password
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
```

### B-2：新建 `erp_qms_core/backend/app/repositories/auth.py`

```python
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
```

### B-3：新建 `erp_qms_core/backend/app/api/v1/auth.py`

```python
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
```

### B-4：在 router.py 加入 auth 路由

修改 `erp_qms_core/backend/app/api/v1/router.py`：

```python
from . import auth, bom, customers, health, inventory, orders, products, shipments, suppliers

router = APIRouter(prefix="/api", tags=["erp-qms-core"])

router.include_router(health.router)
router.include_router(auth.router)       # ← 新增這行
router.include_router(customers.router)
router.include_router(suppliers.router)
router.include_router(products.router)
router.include_router(bom.router)
router.include_router(orders.router)
router.include_router(inventory.router)
router.include_router(shipments.router)
```

### B-5：在 schemas `__init__.py` 加入 LoginRequest（可選）

`LoginRequest` 已在 `api/v1/auth.py` 內定義，不需額外加入 schemas。

### 完成標準

```bash
cd erp_qms_core/backend
ERP_QMS_CORE_JWT_SECRET="test-secret" python run_core.py &
# 在另一個 terminal：
curl -s -X POST http://127.0.0.1:8895/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"emp_no":"A001","password":"wrong"}' | python3 -m json.tool
# 預期：{"detail": "帳號或密碼錯誤。"}

# 如果有測試使用者：
curl -s -X POST http://127.0.0.1:8895/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"emp_no":"admin","password":"admin123"}' | python3 -m json.tool
# 預期：{"access_token": "eyJ...", "token_type": "bearer", "user": {...}}
```

### 結果記錄

```
# AI Agent 填寫：
新建檔案：
修改檔案：
login 端點測試結果：
```

---

## Task C：在現有路由加上 RBAC 保護

**狀態：** [ ] 待執行

### 前置說明

`security.py` 的 `require_roles()` 已設計為 FastAPI dependency factory，
套用方式有兩種：

```python
# 方式一：整個 router 套用同一組角色
router = APIRouter(dependencies=[Depends(require_roles("admin", "qm"))])

# 方式二：單一路由套用
@router.delete("/{id}", dependencies=[Depends(require_roles("admin"))])
def delete_item(id: str): ...
```

### 角色設計

依你們工廠實際職務，定義以下角色碼（role_code）：

| role_code | 中文名稱 | 可存取的主要 API |
|---|---|---|
| `admin` | 系統管理員 | 全部 |
| `qm` | 品保/品管人員 | 全部 QMS / SPC 相關 |
| `prod` | 生產主管/線長 | 工單查詢、庫存查詢（唯讀為主） |
| `mgmt` | 高階主管 | KPI 查詢（唯讀） |

### 需修改的 API 檔案

#### `erp_qms_core/backend/app/api/v1/orders.py`

在 DELETE / 狀態更新路由加上角色保護，查詢路由開放已登入者：

```python
from fastapi import APIRouter, Depends
from ...core.security import require_roles

router = APIRouter(prefix="/orders")

# 查詢：所有登入角色可用
@router.get("/sales-orders", dependencies=[Depends(require_roles())])
def list_sales_orders(): ...

# 狀態更新：限 qm 和 admin
@router.patch("/sales-orders/{id}/status",
              dependencies=[Depends(require_roles("admin", "qm"))])
def update_sales_order_status(id: str, ...): ...
```

**具體要求：**

1. 所有 `GET`（查詢）路由：加 `Depends(require_roles())`（任何登入角色均可，只驗 token）
2. 所有 `POST`（建立）路由：加 `Depends(require_roles("admin", "qm"))`
3. 所有 `PATCH`/`PUT`（更新）路由：加 `Depends(require_roles("admin", "qm"))`
4. 沒有 DELETE 路由（系統規則：軟刪除，不提供 DELETE API）

需修改的 API 檔案：
- `api/v1/customers.py`
- `api/v1/suppliers.py`
- `api/v1/products.py`
- `api/v1/orders.py`
- `api/v1/inventory.py`
- `api/v1/shipments.py`
- `api/v1/bom.py`

`api/v1/health.py` **不加保護**（健康檢查端點必須公開）。

### 整合測試：補充認證相關測試

在 `erp_qms_core/backend/tests/integration/test_core_smoke.py` 加入：

```python
class AuthSmokeTest(unittest.TestCase):
    """驗證 login → token → 保護路由的完整流程。"""

    def setUp(self):
        import os, tempfile
        from pathlib import Path
        self.tmpdir = tempfile.TemporaryDirectory()
        db_path = Path(self.tmpdir.name) / "auth.db"
        os.environ["ERP_QMS_CORE_DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"
        os.environ["ERP_QMS_CORE_JWT_SECRET"] = "test-secret-auth-smoke"

        from erp_qms_core.backend.app.core import db as db_module
        db_module.reset_engine()
        db_module.create_dev_schema()

        from erp_qms_core.backend.app.main import app
        from fastapi.testclient import TestClient
        self.client = TestClient(app)

        # 建立測試使用者
        from erp_qms_core.backend.app.core.security import hash_password
        from erp_qms_core.backend.app.core.db import session_scope
        from erp_qms_core.backend.app.models.master import Role, User
        with session_scope() as s:
            role = Role(id="role-qm-001", role_code="qm", role_name="品管人員")
            s.add(role)
            user = User(
                id="user-test-001",
                emp_no="T001",
                name="測試品管",
                role_id="role-qm-001",
                password_hash=hash_password("test-password"),
                is_active=True,
            )
            s.add(user)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_login_success_returns_token(self):
        resp = self.client.post("/api/auth/login",
                                json={"emp_no": "T001", "password": "test-password"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["token_type"], "bearer")
        self.assertEqual(data["user"]["emp_no"], "T001")

    def test_login_wrong_password_returns_401(self):
        resp = self.client.post("/api/auth/login",
                                json={"emp_no": "T001", "password": "wrong"})
        self.assertEqual(resp.status_code, 401)

    def test_login_unknown_user_returns_401(self):
        resp = self.client.post("/api/auth/login",
                                json={"emp_no": "nobody", "password": "x"})
        self.assertEqual(resp.status_code, 401)

    def test_protected_route_without_token_returns_401(self):
        resp = self.client.get("/api/customers")
        self.assertEqual(resp.status_code, 401)

    def test_protected_route_with_valid_token_succeeds(self):
        # 先登入取 token
        login_resp = self.client.post("/api/auth/login",
                                      json={"emp_no": "T001", "password": "test-password"})
        token = login_resp.json()["access_token"]
        # 帶 token 存取保護路由
        resp = self.client.get("/api/customers",
                               headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(resp.status_code, 200)

    def test_wrong_role_returns_403(self):
        """qm 角色不應能呼叫 admin-only 的路由（如果有設定的話）。"""
        # 此測試在 Task D 設定 admin-only 路由後才有意義
        # 目前先確認 login 成功後 token 的 role 欄位正確
        login_resp = self.client.post("/api/auth/login",
                                      json={"emp_no": "T001", "password": "test-password"})
        token = login_resp.json()["access_token"]
        import jwt
        payload = jwt.decode(token, options={"verify_signature": False})
        self.assertEqual(payload["role"], "qm")
```

### 完成標準

```bash
cd erp_qms_core/backend
ERP_QMS_CORE_JWT_SECRET="test-secret" python -m pytest \
  tests/unit/test_core.py \
  tests/unit/test_domain.py \
  tests/workflows/test_transitions.py \
  tests/integration/test_core_smoke.py \
  -v
# 預期：全部通過，無 regression
```

### 結果記錄

```
# AI Agent 填寫：
修改的路由檔案數：
新增 Auth 測試數：
全測試通過數：
```

---

## Task D：初始化種子資料（Admin 帳號 + 角色）

**狀態：** [ ] 待執行

### 背景

系統首次啟動時，若資料庫是空的，沒有任何使用者可以登入。
需要一個 `seed_admin()` 函式，在開發環境自動建立初始 admin 帳號。

### 新建 `erp_qms_core/backend/app/core/seed.py`

```python
"""
erp_qms_core/backend/app/core/seed.py
開發環境種子資料：初始角色 + admin 帳號。

正式環境：不執行此腳本；改由管理員手動建立帳號或透過管理 API。
"""
from __future__ import annotations

import os

from .db import session_scope
from .security import hash_password
from ..models.master import Role, RolePermission, User


SEED_ROLES = [
    {"id": "role-admin-000", "role_code": "admin", "role_name": "系統管理員"},
    {"id": "role-qm-000",    "role_code": "qm",    "role_name": "品保/品管人員"},
    {"id": "role-prod-000",  "role_code": "prod",   "role_name": "生產主管"},
    {"id": "role-mgmt-000",  "role_code": "mgmt",   "role_name": "高階主管"},
]

SEED_ADMIN = {
    "id":            "user-admin-000",
    "emp_no":        "ADMIN",
    "name":          "系統管理員",
    "role_id":       "role-admin-000",
    "password_hash": None,  # 由環境變數 SEED_ADMIN_PASSWORD 決定
    "is_active":     True,
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
```

### 在 `erp_qms_core/backend/app/core/db.py` 的 `create_dev_schema()` 末尾呼叫

```python
# 在 create_dev_schema() 函式末尾加入：
from .seed import seed_dev
seed_dev()
```

**注意：** 請確認 `create_dev_schema()` 是否存在於 `db.py`（根據 smoke test 的 setUp 可見它存在）。
若函式名稱不同，使用實際名稱。

### 完成標準

```bash
# 啟動 erp_qms_core 服務（開發模式）
cd erp_qms_core/backend
SEED_ADMIN_PASSWORD="admin1234" ERP_QMS_CORE_JWT_SECRET="dev-secret" python run_core.py &

# 用 admin 帳號登入，應成功取得 token
curl -s -X POST http://127.0.0.1:8895/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"emp_no":"ADMIN","password":"admin1234"}' | python3 -m json.tool
# 預期：{"access_token": "eyJ...", "user": {"role_code": "admin", ...}}
```

### 結果記錄

```
# AI Agent 填寫：
seed_dev() 執行結果：
admin 登入測試結果：
```

---

## 執行順序

```
Task A（bcrypt + config）
    ↓
Task B（auth service + login API）
    ↓
Task C（路由加 RBAC）+ Task D（seed 資料）← 可平行
```

Task A 是所有後續任務的前置，必須先完成。
Task B 和 Task C 有依賴關係（C 需要 B 的 token 才能測試）。
Task D 不依賴 C，可與 C 平行執行。

---

## 環境變數備忘

```bash
# 開發環境必填
export ERP_QMS_CORE_JWT_SECRET="請設定一個隨機字串至少32字元"

# 可選（有預設值）
export ERP_QMS_CORE_TOKEN_EXPIRE_MINUTES=480   # 8 小時
export SEED_ADMIN_PASSWORD=admin1234            # 種子 admin 密碼
export JEPE_ENV=development                     # 非 production 才執行 seed
```

---

## 完成後的預期 API 行為

```
POST /api/auth/login             → 公開，回傳 JWT
GET  /api/health                 → 公開（不需 token）
GET  /api/customers              → 需任何有效 token（登入即可）
POST /api/customers              → 需 admin 或 qm 角色
PATCH /api/orders/.../status     → 需 admin 或 qm 角色（+ 狀態機驗證）
```
