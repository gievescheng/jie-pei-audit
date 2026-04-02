# AGENT_TASKS.md
# jie-pei-audit — AI Agent 執行任務清單
# 適用：Claude Code / Codex / 任何可讀取 Markdown 並執行程式碼的 AI Agent
#
# 使用方式：
#   Claude Code: claude --file AGENT_TASKS.md
#   Codex:       直接將此檔案加入 context，再下指令 "請依照任務清單執行 Task 1"
#
# 重要：每完成一個 Task，在對應的 [ ] 打勾變 [x]，並在 ## 結果 區塊記錄產出。

---

## 專案快速定位

```
repo:     https://github.com/gievescheng/jie-pei-audit
本地路徑:  C:\Users\USER\Documents\Codex\自動稽核程式   (Windows)
啟動系統:  啟動系統.bat
```

### 三層架構一覽

| 層 | 目錄 | 職責 | Port |
|---|---|---|---|
| QMS 種子系統 | `v2_backend/` | 文件管理、AI 稽核、SPC、環境監控 | 8888 |
| ERP 主系統骨架 | `erp_qms_core/backend/` | 主資料、訂單、工單、庫存 | 8895 |
| 前端 | `frontend_src/` → `index.html` | React 單頁應用 | — |

### 絕對禁止事項（勿違反）

- **禁止** 刪除或移動 `0 品質手冊/`、`1 文件化資訊管制程序/` 等 QMS 歸檔資料夾
- **禁止** 將 `erp_qms_core` 的 Integer 作為 PK，一律使用 UUID Text
- **禁止** 兩個 Alembic 歷史互相干擾（各自獨立：`v2_backend/alembic.ini`、`erp_qms_core/backend/alembic.ini`）
- **禁止** 一次大改 `audit-dashboard.jsx`；每次只改一個功能塊，改完立即重建 `index.html`
- **禁止** 引入 microservices、替換 FastAPI 或 SQLAlchemy

---

## Task 1：補齊 erp_qms_core domain 測試 ⚡ 最優先

**狀態：** [ ] 待執行

### 背景

`erp_qms_core/backend/tests/unit/`、`integration/`、`workflows/` 目錄目前為空。
`domain/transitions.py` 和 `domain/rules.py` 是整個狀態機的核心邏輯，
沒有測試覆蓋，之後擴充時極易靜默破壞現有流程。

### 目標檔案

```
erp_qms_core/backend/tests/unit/test_domain.py       ← 新建
erp_qms_core/backend/tests/workflows/test_transitions.py  ← 新建（已有此路徑但為空）
```

### 執行規格

#### `test_domain.py` 需覆蓋：

**1. `can_transition()` 合法轉換測試**

所有實體類型（`sales_order`、`work_order`、`shipment`）的每一條合法轉換路徑，
必須各寫一個 `assertTrue` case：

```python
# 範例（其餘類推）
assertTrue(can_transition("sales_order", "draft", "confirmed"))
assertTrue(can_transition("sales_order", "confirmed", "released"))
assertTrue(can_transition("work_order", "draft", "in_progress"))
assertTrue(can_transition("shipment", "draft", "shipped"))
```

**2. `can_transition()` 非法轉換測試**

每個實體類型至少 3 個非法跳轉，必須各寫一個 `assertFalse`：

```python
assertFalse(can_transition("sales_order", "draft", "completed"))   # 跳過中間狀態
assertFalse(can_transition("sales_order", "completed", "draft"))   # 從終態回退
assertFalse(can_transition("work_order", "completed", "in_progress"))
assertFalse(can_transition("shipment", "confirmed", "shipped"))    # 從終態回退
```

**3. 終態測試**

`completed`、`cancelled`、`confirmed`（shipment）都是終態，
`allowed_next()` 回傳的集合必須是空集合：

```python
assertEqual(allowed_next("sales_order", "completed"), set())
assertEqual(allowed_next("sales_order", "cancelled"), set())
assertEqual(allowed_next("work_order", "completed"), set())
assertEqual(allowed_next("shipment", "confirmed"), set())
```

**4. 未知 entity_type 防禦測試**

```python
assertFalse(can_transition("unknown_entity", "draft", "confirmed"))
assertEqual(allowed_next("unknown_entity", "draft"), set())
```

**5. Enum 完整性測試**

確認 `OrderStatus`、`WorkOrderStatus`、`ShipmentStatus` 每個值都有出現在
transitions 表中（沒有遺漏的孤立狀態）：

```python
# 範例
from erp_qms_core.backend.app.domain.enums import OrderStatus
from erp_qms_core.backend.app.domain.transitions import SALES_ORDER_TRANSITIONS
for status in OrderStatus:
    assertIn(status.value, SALES_ORDER_TRANSITIONS)
```

#### `test_transitions.py`（workflows）需覆蓋：

完整的業務生命週期流程，每個流程一個測試方法：

- `test_sales_order_happy_path`：draft → confirmed → released → completed
- `test_sales_order_cancel_at_confirmed`：draft → confirmed → cancelled
- `test_work_order_happy_path`：draft → in_progress → completed
- `test_shipment_happy_path`：draft → shipped → confirmed
- `test_cannot_skip_states`：draft → completed 應該失敗（非法跳躍）

每個流程測試必須用 `can_transition()` 逐步驗證每一跳，不允許只測首尾。

### 執行指令

```bash
cd erp_qms_core/backend
python -m pytest tests/unit/test_domain.py tests/workflows/test_transitions.py -v
```

### 完成標準

- 所有測試通過（0 failures）
- 至少 25 個 test cases 合計

### 結果記錄

```
# AI Agent 填寫：
測試數量：
通過數：
失敗數（及原因）：
```

---

## Task 2：將 spc_engine.py 整合進 v2_backend ⚡ 第二優先

**狀態：** [ ] 待執行

### 背景

目前 repo 有**兩條平行的 SPC 計算路徑**，造成維護風險：

| 路徑 | 位置 | 實作方式 |
|---|---|---|
| **舊路徑（問題所在）** | `v2_backend/app/engines.py` → `compute_spc_metrics()` | 用 Python `statistics` 標準庫，只算 mean/stdev，**沒有 I-MR、Laney u'、Nelson Rules** |
| **正確路徑（已驗證）** | `spc_engine.py`（repo 根目錄） | numpy 實作，含 I-MR、Laney u'、Cpk CI、Nelson Rules 1-6，**48 個測試全通過** |

目標：讓 `v2_backend/app/api.py` 的 `/api/v2/spc/analyze` 路由使用正確的 `spc_engine.py`，
淘汰 `engines.compute_spc_metrics()`。

### 步驟 1：移動 spc_engine.py

將 `spc_engine.py`（repo 根目錄）複製到：

```
v2_backend/app/spc_engine.py
```

**不要刪除根目錄的版本**（其他工具可能參考），複製即可。

確認 `v2_backend/requirements-v2.txt` 包含：

```
numpy>=1.24.0
scipy>=1.11.0
```

若缺少，補上。

### 步驟 2：修改 v2_backend/app/services.py

找到 `analyze_spc()` 函式（約第 353 行），將其改寫為：

```python
def analyze_spc(session, request) -> dict:
    """SPC 分析 — 使用 spc_engine.py 的完整實作（I-MR + Laney u' + Nelson Rules）。"""
    from .spc_engine import run_imr, calc_capability

    prompt = resolve_prompt(session, "spc_analyze")
    values = engines.parse_numeric_values(request.values, request.csv_text)

    # 使用正確的 spc_engine 計算
    imr_result = run_imr(
        values=values,
        usl=request.usl,
        lsl=request.lsl,
        target=request.target,
        chart_id=request.parameter_name,
    )

    # 將 spc_engine 結果轉換成 v2 API 回應格式
    cap = imr_result.get("capability", {})
    metrics = {
        "count":            imr_result["n"],
        "mean":             imr_result["x_bar"],
        "stdev":            imr_result["sigma_mr"],   # MR 法估計 sigma（比 statistics.stdev 更穩健）
        "x_ucl":            imr_result["x_ucl"],
        "x_lcl":            imr_result["x_lcl"],
        "mr_ucl":           imr_result["mr_ucl"],
        "lsl":              request.lsl,
        "usl":              request.usl,
        "target":           request.target,
        "cp":               cap.get("cp"),
        "cpk":              cap.get("cpk"),
        "cpm":              cap.get("cpm"),
        "cpk_ci":           cap.get("cpk_ci"),
        "cpk_grade":        cap.get("grade"),
        "out_of_control_x": imr_result["ooc_x"],
        "out_of_control_mr": imr_result["ooc_mr"],
        "nelson_signals":   imr_result["nelson_signals"],
        "warnings":         imr_result["warnings"],
    }
    abnormal_items = [
        {"index": i + 1, "value": v, "type": "ooc_x"}
        for i, v in enumerate(imr_result["x_values"])
        if i in imr_result["ooc_x"]
    ]

    engineering_summary, management_summary = engines.build_spc_summaries(
        request.parameter_name, metrics, abnormal_items
    )

    llm_summary = adapters.maybe_call_openrouter(
        system_prompt=prompt["system_prompt"],
        policy_prompt=prompt["policy_prompt"],
        user_prompt=(
            prompt["user_prompt_template"]
            + "\n\nMetrics:\n"
            + json.dumps(metrics, ensure_ascii=False, indent=2)
            + "\n\nNelson Signals:\n"
            + json.dumps(imr_result["nelson_signals"], ensure_ascii=False, indent=2)
        ),
    )
    if llm_summary:
        management_summary = llm_summary

    return {
        "parameter_name":     request.parameter_name,
        "metrics":            metrics,
        "abnormal_items":     abnormal_items,
        "engineering_summary": engineering_summary,
        "management_summary":  management_summary,
        "prompt_version":     prompt["version"],
        "citations":          [],
        "source_document_ids": [],
        "tool_outputs_used":  ["spc_engine_v2"],
        "needs_human_review": True,
    }
```

**注意：** `engines.compute_spc_metrics()` 和 `engines.build_spc_summaries()` 分別廢棄和保留：
- `compute_spc_metrics` → 不再呼叫，但**暫時保留函式本體**（不刪除），避免破壞其他引用
- `build_spc_summaries` → 繼續使用

### 步驟 3：在 v2_backend 測試中驗證整合

在 `v2_backend/tests/test_v2_smoke.py` 加入以下測試（仿照現有測試風格）：

```python
def test_spc_analyze_uses_spc_engine(self):
    """確認 /api/v2/spc/analyze 回傳 spc_engine_v2 的標記，且包含 I-MR 管制界限。"""
    payload = {
        "parameter_name": "Thickness",
        "values": [702.1, 701.3, 703.0, 700.8, 702.5,
                   701.9, 703.2, 699.5, 702.8, 701.1,
                   702.4, 701.7, 703.1, 700.6, 702.9],
        "lsl": 695.0,
        "usl": 705.0,
    }
    resp = self.client.post("/api/v2/spc/analyze", json=payload)
    self.assertEqual(resp.status_code, 200)
    data = resp.json()["data"]
    self.assertIn("spc_engine_v2", data["tool_outputs_used"])
    self.assertIn("x_ucl", data["metrics"])
    self.assertIn("x_lcl", data["metrics"])
    self.assertIn("cpk", data["metrics"])
    self.assertIsNotNone(data["metrics"]["cpk"])


def test_spc_analyze_detects_ooc(self):
    """確認明顯失控點能被偵測到。"""
    values = [700.0] * 14 + [710.0]   # 最後一點明顯超出
    payload = {"parameter_name": "Test", "values": values, "usl": 705.0, "lsl": 695.0}
    resp = self.client.post("/api/v2/spc/analyze", json=payload)
    self.assertEqual(resp.status_code, 200)
    data = resp.json()["data"]
    self.assertGreater(len(data["metrics"]["out_of_control_x"]), 0)
```

### 執行指令

```bash
# 1. 確認 numpy/scipy 安裝
pip install numpy scipy

# 2. 跑整合測試
cd v2_backend
python -m pytest tests/test_v2_smoke.py -v -k "spc"
```

### 完成標準

- `/api/v2/spc/analyze` 回傳 `tool_outputs_used: ["spc_engine_v2"]`
- 回傳的 `metrics` 包含 `x_ucl`、`x_lcl`、`cpk`、`nelson_signals`
- 兩個新增測試全部通過

### 結果記錄

```
# AI Agent 填寫：
spc_engine.py 複製位置：
修改的函式：
測試結果：
```

---

## Task 3：為 update_work_order_status 加入狀態機驗證

**狀態：** [ ] 待執行

### 背景

`erp_qms_core/backend/app/services/work_orders.py` 的 `update_work_order_status()` 目前
直接寫入新狀態，**沒有呼叫 `can_transition()` 驗證**，讓非法狀態跳轉可以成功。
`sales_orders.py` 和 `shipments.py` 的同類函式也有相同問題。

### 需修改的三個 service 函式

#### `erp_qms_core/backend/app/services/work_orders.py`

找到 `update_work_order_status()`，在寫入前加入驗證：

```python
from ..domain.transitions import can_transition
from ..core.errors import HTTPException   # 或專案現有的 HTTP 例外類別

def update_work_order_status(wo_id: str, payload: StatusUpdate) -> dict:
    with session_scope() as session:
        row = repo.get_work_order(session, wo_id)
        if not row:
            raise not_found_error("work order")
        # ── 新增：狀態機驗證 ─────────────────────────────────────────
        if not can_transition("work_order", row.wo_status, payload.status):
            raise HTTPException(
                status_code=422,
                detail=f"無法從 '{row.wo_status}' 轉換為 '{payload.status}'。"
                       f" 請確認工單目前狀態允許此操作。"
            )
        # ─────────────────────────────────────────────────────────────
        row.wo_status = payload.status
        return ok({"id": row.id, "wo_no": row.wo_no, "wo_status": row.wo_status}, message="updated")
```

用相同模式修改：
- `erp_qms_core/backend/app/services/sales_orders.py` → `update_sales_order_status()`，entity_type = `"sales_order"`
- `erp_qms_core/backend/app/services/shipments.py` → `update_shipment_status()`，entity_type = `"shipment"`

**注意：** 確認 `erp_qms_core/backend/app/core/errors.py` 中 HTTP 例外的實際匯入路徑，
使用專案現有的錯誤處理方式，不要引入新套件。

### 需新增的測試

在 `erp_qms_core/backend/tests/integration/test_core_smoke.py`
（或新建 `tests/integration/test_transition_guard.py`）加入：

```python
def test_work_order_illegal_transition_is_rejected(self):
    """completed → in_progress 是非法轉換，API 必須回傳 422。"""
    # 建立工單並推進到 completed
    # ... 依現有測試的 client fixture 方式建立

def test_work_order_legal_transition_succeeds(self):
    """draft → in_progress 是合法轉換，API 必須回傳 200。"""
    # ...
```

### 完成標準

- 對三個 service 的非法轉換呼叫均回傳 422
- 合法轉換仍正常回傳 200
- Task 1 的 domain 測試仍然全部通過（不能破壞）

### 結果記錄

```
# AI Agent 填寫：
修改的檔案：
新增測試：
```

---

## Task 4：v2_backend API Key 臨時安全層

**狀態：** [ ] 待執行

### 背景

`v2_backend/app/api.py` 的所有路由目前無認證保護。
在正式 JWT 完成前，加入一個最輕量的 API Key middleware 作為基礎防護。

### 步驟

#### 1. 在 `v2_backend/app/config.py` 加入設定

```python
# 在現有 Settings class 加入：
internal_api_key: str = Field(default="", env="INTERNAL_API_KEY")
```

#### 2. 新建 `v2_backend/app/auth.py`

```python
"""
v2_backend/app/auth.py
最輕量的 API Key 驗證 dependency。
正式 JWT/RBAC 上線後，此模組可直接替換。
"""
from fastapi import Header, HTTPException
from .config import settings


def require_api_key(x_api_key: str = Header(default="")):
    """
    若環境變數 INTERNAL_API_KEY 有設定，則要求 Header 中的 X-Api-Key 匹配。
    若 INTERNAL_API_KEY 未設定（空字串），則跳過驗證（開發模式）。
    """
    if not settings.internal_api_key:
        return   # 開發模式：不驗證
    if x_api_key != settings.internal_api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")
```

#### 3. 在 `v2_backend/app/api.py` 套用 dependency

在 `router = APIRouter(...)` 那一行改為：

```python
from .auth import require_api_key

router = APIRouter(
    prefix="/api/v2",
    tags=["v2"],
    dependencies=[Depends(require_api_key)],  # ← 新增
)
```

確認 `from fastapi import APIRouter, Depends, Query` 的 import 包含 `Depends`。

#### 4. 在 `v2_backend/tests/test_flask_security.py` 加入測試

```python
def test_api_key_required_when_configured(self):
    """若設定了 INTERNAL_API_KEY，無 key 的請求應回傳 401。"""
    import os
    os.environ["INTERNAL_API_KEY"] = "test-secret-key"
    # ... 重新初始化 app 或模擬 header 缺失的請求
    # 清除環境變數
    del os.environ["INTERNAL_API_KEY"]
```

### 完成標準

- 設定 `INTERNAL_API_KEY=test-key` 後，無 Header 的請求回傳 401
- 帶正確 `X-Api-Key: test-key` Header 的請求正常通過
- 未設定 `INTERNAL_API_KEY` 時，所有請求不受影響（向下相容）

### 結果記錄

```
# AI Agent 填寫：
```

---

## Task 5：01_data.jsx 初步拆分

**狀態：** [ ] 待執行

### 背景

`frontend_src/01_data.jsx`（87KB）同時包含靜態常數、API 呼叫邏輯，
導致任何功能修改都要在這個龐大檔案裡尋找入口。

### 規格

**注意：此 Task 風險較高。每完成一個子步驟後，必須執行 `python build_html.py` 並確認 `index.html` 在瀏覽器可正常顯示，再繼續下一步。**

#### 步驟 1：新建 `frontend_src/00_constants.jsx`

從 `01_data.jsx` 中識別所有**純靜態常數**（不包含函式、不呼叫 API），
將它們移到 `00_constants.jsx`。

典型的靜態常數特徵：
- `const XXX = { ... }` 或 `const XXX = [...]`
- 內容是字串、數字、布林、物件字面量
- 不包含 `fetch`、`await`、`useState`、`useEffect`

移完後，在 `01_data.jsx` 頂部加入（若 build 系統支援模組匯入）：
```js
// 常數已移至 00_constants.jsx，由 build_html.py 合併
```

並在 `frontend_src/manifest.txt` 的最前面加入 `00_constants.jsx`。

#### 步驟 2：驗證

```bash
python build_html.py
# 開啟瀏覽器確認 http://127.0.0.1:8888/ 正常
# 確認所有 Tab 可切換
# 確認文件管理、不符合管理、稽核計畫三個主功能可操作
```

### 完成標準

- `00_constants.jsx` 建立，包含從 `01_data.jsx` 提取的靜態常數
- `01_data.jsx` 大小從 87KB 減少至 75KB 以下
- `index.html` 重建後所有頁面功能正常
- **不允許** 任何 JavaScript 執行錯誤（打開瀏覽器 Console 確認）

### 結果記錄

```
# AI Agent 填寫：
01_data.jsx 原始大小：87KB
01_data.jsx 拆分後大小：
00_constants.jsx 大小：
build 結果：
```

---

## Task 6：文件版次比對結果持久化（可選，中期）

**狀態：** [ ] 待執行

### 背景

`/api/v2/documents/compare` 每次都是即時計算，稽核員無法查看歷史比對記錄。
加入 `CompareResult` 資料模型，讓比對結果可以存儲和查詢。

### 步驟

#### 1. 在 `v2_backend/app/models.py` 加入新 Model

```python
class CompareResult(Base):
    __tablename__ = "compare_results"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    left_document_id: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
    right_document_id: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
    left_title: Mapped[str] = mapped_column(Text, default="")
    right_title: Mapped[str] = mapped_column(Text, default="")
    similarity: Mapped[float] = mapped_column(Text, default=0.0)  # 使用 Float 類型
    added_count: Mapped[int] = mapped_column(Integer, default=0)
    removed_count: Mapped[int] = mapped_column(Integer, default=0)
    conclusion_json: Mapped[str] = mapped_column(Text, default="{}")  # JSON string
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    created_by: Mapped[str] = mapped_column(Text, default="system")
```

#### 2. 建立對應 Alembic migration

```bash
cd v2_backend
alembic revision --autogenerate -m "add_compare_results"
alembic upgrade head
```

#### 3. 在 `compare_documents` service 函式末尾加入儲存邏輯

在 `v2_backend/app/services.py` 的 `compare_documents()` 函式，
計算完畢後將結果寫入 `compare_results` 表。

#### 4. 新增 GET `/api/v2/documents/compare/history` 端點

回傳最近 50 筆比對記錄（分頁）。

### 完成標準

- 每次呼叫 `/api/v2/documents/compare` 後，資料庫有新記錄
- `/api/v2/documents/compare/history` 可查詢歷史記錄

---

## 執行優先順序

```
Task 1（domain 測試）  ──→  Task 2（SPC 整合）  ──→  Task 3（狀態機驗證）
                                                           │
                                               Task 4（API Key）  Task 5（前端拆分）
                                                           │
                                                    Task 6（比對歷史，可選）
```

Task 1 和 Task 2 是最高優先，且彼此獨立可平行執行。
Task 3 依賴 Task 1 完成（需要 domain 測試作為迴歸保護）。
Task 5 任何時候都可以獨立做，但每一步必須重建並驗證 `index.html`。

---

## 環境設定備忘

```bash
# 安裝 erp_qms_core 相依
cd erp_qms_core/backend
pip install -r requirements-dev.txt
pip install numpy scipy   # Task 2 需要

# 執行 erp_qms_core 全部測試
python -m pytest tests/ -v

# 執行 v2_backend 全部測試
cd v2_backend
python -m pytest tests/ -v

# 重建前端
python build_html.py
```

---

## 完成後的預期狀態

| 檔案/功能 | Task 1 後 | Task 2 後 | Task 3 後 |
|---|---|---|---|
| domain 測試覆蓋 | ✅ 25+ cases | 不變 | 不變 |
| `/api/v2/spc/analyze` | 不變 | ✅ 使用 spc_engine | 不變 |
| 狀態機非法跳轉 | 仍可成功（Bug） | 不變 | ✅ 回傳 422 |
| API 認證 | 無 | 無 | 無 | Task 4 後 ✅ |
| `01_data.jsx` 大小 | 87KB | 87KB | 87KB | Task 5 後 < 75KB |
