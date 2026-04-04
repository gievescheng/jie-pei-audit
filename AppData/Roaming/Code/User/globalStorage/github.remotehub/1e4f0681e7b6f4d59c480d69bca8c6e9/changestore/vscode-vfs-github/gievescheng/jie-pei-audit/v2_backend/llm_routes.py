"""LLM routes for v2_backend (Flask blueprint)

提供 /api/llm/generate 路由：
- POST /api/llm/generate
  JSON body: {"prompt":"...", "mode":"http"|"hf", "base_url":"...", "model":"...", "live": true|false }

若 live=false（預設），回傳將要呼叫的 endpoint/payload（不會真正呼叫）。
若 live=true，會嘗試用建立的 connector 執行 `generate` 並回傳結果。
"""
from __future__ import annotations

from flask import Blueprint, request, jsonify
from typing import Any, Dict

from v2_backend.llm_service import get_connector_from_cfg

llm_bp = Blueprint("llm", __name__, url_prefix="/api/llm")


@llm_bp.route("/generate", methods=["POST"])
def generate_route():
    body: Dict[str, Any] = request.get_json(force=True) or {}
    prompt = body.get("prompt", "")
    live = bool(body.get("live", False))
    cfg: Dict[str, Any] = {}
    # optional config keys
    for k in ("mode", "base_url", "model", "api_key", "chat", "device"):
        if k in body:
            cfg[k] = body[k]
    try:
        conn = get_connector_from_cfg(cfg)
    except Exception as e:
        return jsonify({"error": "connector_init_failed", "detail": str(e)}), 500

    if not live:
        # 回傳預期的 endpoint 或模型資訊
        if getattr(conn, "mode", "http") == "http":
            base = conn.kwargs.get("base_url", "")
            is_chat = bool(conn.kwargs.get("chat", True))
            endpoint = base.rstrip("/") + ("/v1/chat/completions" if is_chat else "/v1/completions")
            payload = {
                "messages": [{"role": "user", "content": prompt}] if is_chat else {"prompt": prompt, "temperature": 0.7, "max_tokens": 512}
            }
            return jsonify({"endpoint": endpoint, "payload": payload})
        else:
            return jsonify({"info": "hf_mode_configured", "model": conn.kwargs.get("model")})

    # live 呼叫
    try:
        out = conn.generate(prompt)
        return jsonify({"result": out})
    except Exception as e:
        return jsonify({"error": "generation_failed", "detail": str(e)}), 500
