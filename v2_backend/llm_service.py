"""v2_backend LLM service integration

提供簡易介面供 v2_backend 其他模組取得 LocalModelConnector
"""
from typing import Any, Dict
import pathlib


# 優先透過 package 匯入，若失敗則從檔案載入
try:
    from v2_backend.llm_adapter import create_connector_from_config
except Exception:
    try:
        from llm_adapter import create_connector_from_config
    except Exception:
        import importlib.util
        root = pathlib.Path(__file__).resolve().parents[1]
        adapter_path = root / "v2_backend" / "llm_adapter.py"
        spec = importlib.util.spec_from_file_location("v2_backend.llm_adapter", str(adapter_path))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        create_connector_from_config = module.create_connector_from_config


def get_connector_from_cfg(cfg: Dict[str, Any] | None = None):
    """建立一個 LocalModelConnector

    cfg 範例: {"mode":"http","base_url":"http://localhost:8000","chat":True}
    """
    if cfg is None:
        cfg = {"mode": "http", "base_url": "http://localhost:8000", "chat": True}
    return create_connector_from_config(cfg)


def attach_to_app(app: Any, cfg: Dict[str, Any] | None = None):
    """把 connector 附到簡單的 app 物件上 (app.llm)"""
    app.llm = get_connector_from_cfg(cfg)
    return app.llm


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--base_url", default="http://localhost:8000")
    parser.add_argument("--prompt", default="測試")
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()

    conn = get_connector_from_cfg({"mode": "http", "base_url": args.base_url, "chat": True})
    print("Connector:", type(conn), "kwargs=", getattr(conn, "kwargs", None))
    if args.live:
        try:
            out = conn.generate(args.prompt)
            print("Response:\n", out)
        except Exception as e:
            print("Live call failed:", e)
