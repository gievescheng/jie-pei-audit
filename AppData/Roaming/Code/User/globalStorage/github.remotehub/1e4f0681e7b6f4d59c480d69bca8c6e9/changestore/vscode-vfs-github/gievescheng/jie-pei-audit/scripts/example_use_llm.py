#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""示例：示範如何使用 LocalModelConnector（預設非 live，僅顯示 payload）

使用方式：
  python scripts/example_use_llm.py --prompt "測試文字"
  python scripts/example_use_llm.py --prompt "測試" --live  # 若本地有運行 LLM http 服務
"""

import argparse
import json
import pathlib


def import_local_connector():
    try:
        # 優先從 package import（在 repo 環境中）
        from scripts.local_model_connector import LocalModelConnector
        return LocalModelConnector
    except Exception:
        # fallback: 嘗試從 repo scripts 資料夾載入同名檔案
        import importlib.util, sys
        p = pathlib.Path(__file__).resolve().parent / "local_model_connector.py"
        if p.exists():
            spec = importlib.util.spec_from_file_location("local_model_connector", str(p))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module.LocalModelConnector
        # 最後嘗試在 CWD 匯入 local_model_connector
        try:
            import local_model_connector as _lm
            return _lm.LocalModelConnector
        except Exception as e:
            print("無法載入 LocalModelConnector:", e)
            raise SystemExit(1)


def demo_http(LocalModelConnector, base_url: str, prompt: str, live: bool = False):
    conn = LocalModelConnector(mode="http", base_url=base_url, chat=True)
    if live:
        try:
            print("執行實際呼叫...")
            out = conn.generate(prompt)
            print("伺服器回應:\n", out)
        except Exception as e:
            print("實際呼叫失敗:", type(e).__name__, e)
            print("請確認本地 LLM 伺服器是否在運行，或改用非 live 模式以檢視 payload。")
    else:
        payload = {"messages": [{"role": "user", "content": prompt}], "temperature": 0.7, "max_tokens": 512}
        if conn.kwargs.get("model"):
            payload["model"] = conn.kwargs["model"]
        endpoint = base_url.rstrip("/") + "/v1/chat/completions"
        print("非 live 模式 - 將呼叫以下 endpoint & payload：")
        print(endpoint)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        print("如要實際呼叫，請加上 --live 並確認本地 LLM 服務運作。")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base_url", default="http://localhost:8000")
    parser.add_argument("--prompt", default="測試輸入")
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    LocalModelConnector = import_local_connector()
    demo_http(LocalModelConnector, args.base_url, args.prompt, live=args.live)


if __name__ == '__main__':
    main()
