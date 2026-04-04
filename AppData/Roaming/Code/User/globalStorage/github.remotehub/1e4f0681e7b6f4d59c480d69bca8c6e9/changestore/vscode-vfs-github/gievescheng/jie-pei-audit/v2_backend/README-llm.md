LLM 路由使用說明

此文件說明如何使用已加入的 LLM 路由：`/api/llm/generate`。

路由摘要
- POST /api/llm/generate
  - JSON body 範例（非 live 模式）：
    {
      "prompt": "請幫我寫一段中文摘要",
      "mode": "http",
      "base_url": "http://localhost:8000",
      "chat": true
    }
  - 若 `live` 設為 `false`（預設），API 會回傳將要呼叫的 endpoint / payload（不實際呼叫）。
  - 若 `live` 設為 `true`，API 會嘗試以建立的 connector 執行 `generate` 並回傳結果（請確保本地 LLM 可用）。

快速安裝與啟動（PowerShell 範例）

```powershell
python -m venv .venv
.\.venv\Scripts\Activate
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -r requirements-local-model.txt
.\.venv\Scripts\python -m pip install flask

# 啟動方式 A（直接執行 server.py）
.\.venv\Scripts\python server.py

# 或方式 B（使用 Flask CLI）
$env:FLASK_APP = "server.py"
.\.venv\Scripts\python -m flask run --host=127.0.0.1 --port=5000
```

cURL 範例

- 非 live（檢視將送出的 endpoint 與 payload）：

```bash
curl -s -X POST http://localhost:5000/api/llm/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"請幫我寫一段中文摘要","mode":"http","base_url":"http://localhost:8000","chat":true}'
```

- live（會實際呼叫 base_url 指向的 LLM 伺服器）：

```bash
curl -s -X POST http://localhost:5000/api/llm/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"測試","mode":"http","base_url":"http://localhost:8000","chat":true,"live":true}'
```

- Hugging Face 本地模型（若要在 server 端以 HF 模式直接載入模型）：

```bash
curl -s -X POST http://localhost:5000/api/llm/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"寫一句中文","mode":"hf","model":"gpt2","live":true}'
```

注意事項
- HTTP 模式：請確保 `base_url` 指向一個 OpenAI-compatible 的本地/自架 HTTP LLM 伺服器（含 /v1/chat/completions 或 /v1/completions）。
- HF 模式：若 `live=true`，server 需要安裝 `transformers` 與 `torch` 並有足夠的資源載入模型。
- 若要在專案內用程式呼叫，範例參考 `scripts/example_use_llm.py`。

相關檔案
- 路由實作：[v2_backend/llm_routes.py](v2_backend/llm_routes.py)
- 專案整合介面：[v2_backend/llm_service.py](v2_backend/llm_service.py)
- 使用範例腳本：[scripts/example_use_llm.py](scripts/example_use_llm.py)

問題排查
- 若回傳 `connector_init_failed`，請確認提供的 `base_url` / `model` 格式正確。
- 若 live 呼叫失敗，先以非 live 模式檢視 payload，或檢查本地 LLM 伺服器日誌。
