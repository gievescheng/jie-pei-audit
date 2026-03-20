# JEPE ERP-QMS Core Bootstrap

這個資料夾是「正式 ERP-QMS 主系統」的起跑點，不是用來取代目前可用的 `自動稽核程式`。

## 角色定位

- `自動稽核程式`：QMS 種子系統、流程驗證平台、文件/稽核/AI 工作台。
- `erp_qms_core`：未來正式 ERP-QMS 主系統的骨架，負責交易核心、主資料、權限、審計軌跡。

## 目前已落地的內容

- FastAPI 後端骨架
- SQLAlchemy 核心資料模型初版
- Alembic migration 初版
- 基本主資料與交易 API
- 與現有種子系統的模組分工說明

## 這一版刻意不做的事

- 不搬動現有 `audit-dashboard.jsx` 畫面
- 不直接接入現有 Flask UI
- 不一次做完整 ERP 流程
- 不在這一版加入 Redis / Celery / Docker Compose

## 建議使用方式

1. 繼續在 `自動稽核程式` 上補 QMS 高價值功能。
2. 同步在這裡建立正式主資料、訂單、工單、庫存、權限模型。
3. 等主系統交易核心穩定後，再把現有種子系統的 QMS 能力逐步接入。
