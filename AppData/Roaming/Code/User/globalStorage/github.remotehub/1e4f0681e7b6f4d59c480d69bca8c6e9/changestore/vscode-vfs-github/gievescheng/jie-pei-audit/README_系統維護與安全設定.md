# 自動稽核系統維護與安全設定

這份文件是給不熟程式的人看的，目的是讓你知道系統現在怎麼啟動、重要設定放哪裡、哪些檔案不能外流。

## 1. 啟動方式

平常只要執行：

```text
啟動系統.bat
```

啟動後會有兩個服務：

1. Flask 主站：`http://127.0.0.1:8888/`
2. V2 AI 服務：`http://127.0.0.1:8890/api/v2/health`

預設只允許本機連線。  
如果沒有特殊需求，不要把主機改成 `0.0.0.0`。

## 2. 私有設定檔在哪裡

系統現在會把敏感設定改放到 Windows 的私有資料夾：

```text
%APPDATA%\AutoAudit\
```

裡面可能包含：

1. `v2_runtime.json`
2. `google_calendar_config.json`
3. `google_calendar_tokens.json`
4. `flask_secret.key`

這些檔案不要寄給別人，也不要上傳到雲端公開位置。

## 3. 為什麼不能把設定放在專案資料夾

以前專案根目錄裡的某些檔案，會被網站直接讀到。  
如果把 API key、資料庫連線、Google token 放在那裡，就等於把鑰匙放在門口。

現在已改成：

1. 主站只公開必要前端檔案
2. 敏感設定放到私有資料夾

## 4. PostgreSQL 設定

如果要把 V2 接到 PostgreSQL，可用：

```text
切換V2到PostgreSQL.bat
```

它會要求你輸入連線字串。

完成後，設定會寫到私有設定檔，不會再放在專案根目錄。

## 5. OpenRouter 設定

OpenRouter key 也會放在私有設定檔。  
這個 key 代表可以呼叫模型服務，因此同樣不能外流。

## 6. 資料庫 migration

系統已加入 migration 基礎。

如果之後要初始化或升級 V2 資料庫，可用：

```text
py -3.13 migrate_v2.py
```

簡單理解：

1. migration = 有版本的資料表升級流程
2. 不再靠程式啟動時「順手建表」
3. 這樣之後資料表變動比較安全，也比較容易追蹤

## 7. 備份建議

至少備份兩種東西：

1. PostgreSQL 資料庫
2. `%APPDATA%\AutoAudit\` 這個私有設定資料夾

如果只備份專案資料夾，Google token、V2 設定、secret 可能不在裡面。

## 8. 遇到問題先看什麼

### 主站打不開

先確認：

1. `啟動系統.bat` 是否有跑完
2. `http://127.0.0.1:8888/` 是否能開

### AI 工作台不能用

先確認：

1. `http://127.0.0.1:8890/api/v2/health` 是否回應
2. PostgreSQL 是否正常

### PostgreSQL 連不上

正式模式下，V2 不會再偷偷退回 SQLite。  
這是故意的，因為正式資料庫如果壞了，就應該直接讓你知道。

## 9. 目前系統的使用原則

1. 這套系統目前仍以本機或內網使用為主
2. 不要把整個專案資料夾直接當公開網站目錄
3. 不要把 `%APPDATA%\AutoAudit\` 裡的檔案外流

## 10. LLM 路由使用說明

本節說明如何使用已加入的 LLM 路由：`/api/llm/generate`。

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
- 路由實作：`v2_backend/llm_routes.py`
- 專案整合介面：`v2_backend/llm_service.py`
- 使用範例腳本：`scripts/example_use_llm.py`

問題排查
- 若回傳 `connector_init_failed`，請確認提供的 `base_url` / `model` 格式正確。
- 若 live 呼叫失敗，先以非 live 模式檢視 payload，或檢查本地 LLM 伺服器日誌。
