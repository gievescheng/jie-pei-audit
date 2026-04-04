本地模型連接器（簡介）

檔案
- scripts/local_model_connector.py：主要腳本，支援 `http` 與 `hf` 模式
- requirements-local-model.txt：建議安裝套件

安裝

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements-local-model.txt
```

範例用法（HTTP）

```bash
python scripts/local_model_connector.py --mode http --base_url http://localhost:8000 --prompt "測試用 prompt" --chat
```

範例用法（Hugging Face 本地模型）

```bash
python scripts/local_model_connector.py --mode hf --model gpt2 --prompt "寫一句中文問候"
```

說明
- `http` 模式：用於連接像 OpenAI-compatible 的本地伺服器（例如 OpenLLM、llama.cpp API wrapper、或自架的 API）
- `hf` 模式：直接在本機載入 Transformers 模型（需安裝 `transformers`、`torch`）

下一步建議
- 若要我幫你執行安裝並測試（若你允許），請回覆「請幫我安裝並測試」。
