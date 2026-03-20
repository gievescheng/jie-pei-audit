# ERP-QMS Core Backend

## 目的

這個 backend 是未來正式 ERP-QMS 主系統的最小骨架。

它負責：

- 主資料
- 訂單 / 工單 / 庫存等交易核心
- 權限與審計軌跡的正式資料模型起點

它目前不負責：

- 現有 QMS 種子系統的頁面
- AI 文件稽核工作台
- 現有 Word / Excel 報告 UI

## 啟動

```powershell
cd C:\Users\USER\Documents\Codex\自動稽核程式\erp_qms_core\backend
py -3.13 run_core.py
```

預設服務位置：

- `http://127.0.0.1:8895`

## 開發資料庫

預設會使用：

- `backend/data/erp_qms_core.db`

也可以改用環境變數：

```powershell
$env:ERP_QMS_CORE_DATABASE_URL="postgresql://user:password@127.0.0.1:5432/erp_qms_core"
```

## Migration

```powershell
cd C:\Users\USER\Documents\Codex\自動稽核程式\erp_qms_core\backend
py -3.13 migrate_core.py
```
