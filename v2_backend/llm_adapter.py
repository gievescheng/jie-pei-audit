"""v2_backend LLM Adapter

提供一個小型包裝，方便在 `v2_backend` 中建立 `LocalModelConnector` 實例。
此檔案會嘗試先以普通 import (`scripts.local_model_connector`) 匯入，若失敗則以
相對路徑載入 `scripts/local_model_connector.py`，以增加整合韌性。
"""
from typing import Any, Dict
import pathlib

try:
    from scripts.local_model_connector import LocalModelConnector
except Exception:
    import importlib.util
    root = pathlib.Path(__file__).resolve().parents[1]
    script_path = root / "scripts" / "local_model_connector.py"
    spec = importlib.util.spec_from_file_location("local_model_connector", str(script_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    LocalModelConnector = module.LocalModelConnector


def create_connector_from_config(cfg: Dict[str, Any]) -> LocalModelConnector:
    """根據設定建立並回傳 LocalModelConnector

    期望 cfg 可以包含 keys: `mode`, `base_url`, `model`, `api_key`, `chat`, `device`。
    """
    mode = cfg.get("mode", "http")
    kwargs = {}
    for k in ("base_url", "model", "api_key", "chat", "device"):
        if k in cfg:
            kwargs[k] = cfg[k]
    return LocalModelConnector(mode=mode, **kwargs)


def get_llm(mode: str = "http", base_url: str | None = None, model: str | None = None,
            api_key: str | None = None, chat: bool = False, device: str = "auto") -> LocalModelConnector:
    """快速建立一個 LocalModelConnector 實例（函式介面）"""
    return LocalModelConnector(mode=mode, base_url=base_url, model=model,
                               api_key=api_key, chat=chat, device=device)


__all__ = ["create_connector_from_config", "get_llm"]
