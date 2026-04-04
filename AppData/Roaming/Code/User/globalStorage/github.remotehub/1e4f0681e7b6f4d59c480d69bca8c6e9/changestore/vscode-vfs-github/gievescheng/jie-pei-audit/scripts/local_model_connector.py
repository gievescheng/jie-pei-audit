#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡單的本地模型 / 專案連接器
- 支援 `http` 模式：呼叫本地 OpenAI-compatible API（/v1/completions 或 /v1/chat/completions）
- 支援 `hf` 模式：使用 Hugging Face Transformers pipeline 直接載入本地模型

範例：
  python scripts/local_model_connector.py --mode http --base_url http://localhost:8000 --prompt "說明一下" --chat
  python scripts/local_model_connector.py --mode hf --model gpt2 --prompt "寫一段中文問候"
"""

from typing import Optional
import argparse
import json
import sys

try:
    import requests
except Exception:
    requests = None


def generate_http(base_url: str, prompt: str, model: Optional[str] = None, api_key: Optional[str] = None,
                  chat: bool = False, temperature: float = 0.7, max_tokens: int = 512,
                  timeout: int = 30) -> str:
    """呼叫本地或自架 HTTP LLM 伺服器（OpenAI-compatible）"""
    if requests is None:
        raise RuntimeError("缺少 requests，請執行: pip install requests")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    base = base_url.rstrip("/")
    if chat:
        endpoint = "/v1/chat/completions"
        payload = {"messages": [{"role": "user", "content": prompt}],
                   "temperature": temperature,
                   "max_tokens": max_tokens}
        if model:
            payload["model"] = model
    else:
        endpoint = "/v1/completions"
        payload = {"prompt": prompt, "temperature": temperature, "max_tokens": max_tokens}
        if model:
            payload["model"] = model
    url = f"{base}{endpoint}"
    resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    # 常見回傳解析
    try:
        if chat:
            return data["choices"][0]["message"]["content"]
    except Exception:
        pass
    try:
        return data["choices"][0]["text"]
    except Exception:
        return json.dumps(data, ensure_ascii=False)


def generate_hf(model_name: str, prompt: str, max_new_tokens: int = 256, temperature: float = 0.7,
                top_p: float = 0.9, device: Optional[str] = "auto") -> str:
    """使用 transformers pipeline 本地生成（需安裝 transformers + torch）"""
    try:
        from transformers import pipeline
        import torch
    except Exception as e:
        raise RuntimeError("需要安裝 transformers 與 torch，請執行: pip install transformers torch") from e
    if device == "auto":
        device_idx = 0 if torch.cuda.is_available() else -1
    else:
        try:
            device_idx = int(device)
        except Exception:
            device_idx = -1
    gen = pipeline("text-generation", model=model_name, device=device_idx)
    out = gen(prompt, max_new_tokens=max_new_tokens, temperature=temperature, top_p=top_p, do_sample=True)
    if isinstance(out, list) and out:
        first = out[0]
        if isinstance(first, dict):
            return first.get("generated_text") or first.get("text") or str(first)
    return str(out)


class LocalModelConnector:
    def __init__(self, mode: str = "http", **kwargs):
        self.mode = mode
        self.kwargs = kwargs

    def generate(self, prompt: str, **opts) -> str:
        if self.mode == "http":
            base_url = self.kwargs.get("base_url") or opts.get("base_url")
            if not base_url:
                raise ValueError("http 模式需要提供 base_url")
            return generate_http(base_url=base_url, prompt=prompt,
                                 model=self.kwargs.get("model"), api_key=self.kwargs.get("api_key"),
                                 chat=self.kwargs.get("chat", False), temperature=opts.get("temperature", 0.7),
                                 max_tokens=opts.get("max_tokens", 512))
        elif self.mode == "hf":
            model_name = self.kwargs.get("model") or opts.get("model")
            if not model_name:
                raise ValueError("hf 模式需要提供 model 名稱或路徑")
            return generate_hf(model_name=model_name, prompt=prompt,
                               max_new_tokens=opts.get("max_new_tokens", 256),
                               temperature=opts.get("temperature", 0.7),
                               top_p=opts.get("top_p", 0.9),
                               device=self.kwargs.get("device", "auto"))
        else:
            raise ValueError(f"未知模式: {self.mode}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="本地模型/HTTP 連接器")
    parser.add_argument("--mode", choices=["http", "hf"], default="http", help="http 或 hf")
    parser.add_argument("--base_url", help="本地 API 的 base URL，例如 http://localhost:8000")
    parser.add_argument("--api_key", help="若 API 需要認證，設定 API Key")
    parser.add_argument("--model", help="模型名稱或路徑（hf 模式）或 api model 名稱（http 模式）")
    parser.add_argument("--prompt", required=True, help="要送出的 prompt")
    parser.add_argument("--chat", action="store_true", help="使用 chat endpoint（http 模式）")
    parser.add_argument("--device", default="auto", help="hf 裝置，'auto' 或 -1 表示 CPU，0 表示 GPU")
    parser.add_argument("--max_tokens", type=int, default=512)
    parser.add_argument("--max_new_tokens", type=int, default=256)
    parser.add_argument("--temperature", type=float, default=0.7)
    args = parser.parse_args(argv)
    if args.mode == "http" and not args.base_url:
        parser.error("--mode http 時必須提供 --base_url")
    if args.mode == "hf" and not args.model:
        parser.error("--mode hf 時必須提供 --model")

    conn = LocalModelConnector(mode=args.mode, base_url=args.base_url, api_key=args.api_key, model=args.model, chat=args.chat, device=args.device)
    try:
        out = conn.generate(args.prompt, temperature=args.temperature, max_tokens=args.max_tokens, max_new_tokens=args.max_new_tokens)
    except Exception as e:
        print("執行失敗：", e, file=sys.stderr)
        sys.exit(2)
    print(out)


if __name__ == '__main__':
    main()
