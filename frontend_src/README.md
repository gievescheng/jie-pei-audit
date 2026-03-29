# 前端來源說明

目前系統仍可直接從 `audit-dashboard.jsx` 建置 `index.html`。

如果之後要逐步拆模組，可在這個資料夾新增 `manifest.txt`，每行列出一個來源檔，`build_html.py` 會依序組裝：

```text
# 例子
components/badge.jsx
tabs/ai-workbench.jsx
app.jsx
```

注意：

1. `manifest.txt` 路徑一律相對於 `frontend_src/`
2. 目前只是保留拆分能力，不代表整個前端已完全模組化
3. 若沒有 `manifest.txt`，系統仍使用原本的 `audit-dashboard.jsx`
