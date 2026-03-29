# 潔沛企業有限公司 — ISO 9001:2015 自動稽核系統
# Claude Code Project Context

## Project Overview
單一 HTML 檔案的 React 稽核系統（`index.html`，~312KB）。
後端：`v2_backend/`（FastAPI + SQLAlchemy + Alembic）、`erp_qms_core/`（ERP 主數據）。
詳細架構見 `v2_backend/` 與 `erp_qms_core/` 目錄。

## System Topology
| System | Path | DB | Alembic |
|---|---|---|---|
| v2_backend (QMS) | `v2_backend/` | SQLite dev / PostgreSQL prod | `v2_backend/alembic.ini` |
| erp_qms_core (ERP) | `erp_qms_core/backend/` | PostgreSQL | `erp_qms_core/backend/alembic.ini` |

**Critical:** erp_qms_core PKs are UUID Text — never use Integer FK. The two Alembic histories are independent.

---

## Design Context

### Users
四類使用族群：品保/品管人員（主要操作者）、生產主管/線長（狀態查看）、
高階主管（KPI 儀表板）、外部稽核員（ISO 稽核展示）。

### Brand Personality
**專業 · 可信賴 · 精準**
情緒目標：讓品管人員感到「一切在掌控中」；讓稽核員感到「這家公司認真對待品質」。
參考標竿：Linear（精緻感）+ Notion（清晰感）。

### Aesthetic Direction
- **主題**：深色為主（`#0a0f1e` 背景），規劃加入淺色模式切換
- **主色漸層**：`#3b82f6 → #6366f1`（藍 → 靛）
- **語義色**：`#ef4444`（危急）、`#f59e0b`（警示）、`#22c55e`（正常）— 不可反轉
- **字型**：Noto Sans TC，400/600/700 weight
- **反例**：不要過多彩虹色、裝飾性插圖、圓角 > 18px、傳統白底 ERP 感

### Design Principles
1. **語義先行**：顏色是溝通工具，不是裝飾。每個有色元素必須傳達狀態資訊。
2. **密度可調**：日常操作者需要高密度；高階主管需要摘要視圖。
3. **狀態永遠清晰**：任何記錄，2 秒內判斷其狀態（色塊 + 圖示 + 文字三重冗餘）。
4. **互動有反饋**：按鈕有回應，錯誤說明「怎麼修」不只說「什麼錯」。
5. **雙模式準備度**：新元件須同時定義深/淺色 token。

*完整設計脈絡見 `.impeccable.md`。*
