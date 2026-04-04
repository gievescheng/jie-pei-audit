from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from runtime_paths import PRIVATE_CONFIG_DIR, V2_RUNTIME_CONFIG_PATH, migrate_legacy_private_files


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SERVICE_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = SERVICE_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
RUNTIME_CONFIG_PATH = V2_RUNTIME_CONFIG_PATH
migrate_legacy_private_files()


def load_runtime_config() -> dict:
    if not RUNTIME_CONFIG_PATH.exists():
        return {}
    try:
        return json.loads(RUNTIME_CONFIG_PATH.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


RUNTIME_CONFIG = load_runtime_config()


@dataclass(frozen=True)
class Settings:
    project_root: Path = PROJECT_ROOT
    service_root: Path = SERVICE_ROOT
    private_config_dir: Path = PRIVATE_CONFIG_DIR
    database_url: str = os.getenv("DATABASE_URL") or str(RUNTIME_CONFIG.get("database_url") or f"sqlite:///{(DATA_DIR / 'v2_dev.db').as_posix()}")
    database_policy: str = (os.getenv("V2_DATABASE_POLICY") or str(RUNTIME_CONFIG.get("database_policy") or "dev")).strip().lower()
    openrouter_api_key: str = (os.getenv("OPENROUTER_API_KEY") or str(RUNTIME_CONFIG.get("openrouter_api_key") or "")).strip()
    openrouter_model: str = (os.getenv("OPENROUTER_MODEL") or str(RUNTIME_CONFIG.get("openrouter_model") or "nvidia/nemotron-3-super-120b-a12b:free")).strip()
    openrouter_timeout: int = int(os.getenv("OPENROUTER_TIMEOUT") or str(RUNTIME_CONFIG.get("openrouter_timeout") or "45"))
    ollama_base_url: str = (os.getenv("OLLAMA_BASE_URL") or str(RUNTIME_CONFIG.get("ollama_base_url") or "http://localhost:11434")).strip()
    ollama_model: str = (os.getenv("OLLAMA_MODEL") or str(RUNTIME_CONFIG.get("ollama_model") or "gemma4:latest")).strip()
    ollama_timeout: int = int(os.getenv("OLLAMA_TIMEOUT") or str(RUNTIME_CONFIG.get("ollama_timeout") or "300"))
    host: str = os.getenv("V2_HOST") or str(RUNTIME_CONFIG.get("host") or "127.0.0.1")
    port: int = int(os.getenv("V2_PORT") or str(RUNTIME_CONFIG.get("port") or "8890"))
    # ERP bridge — set ERP_BASE_URL to enable live resolution of ERP master data
    # e.g. "http://127.0.0.1:8000"  (erp_qms_core FastAPI instance)
    erp_base_url: str | None = (os.getenv("ERP_BASE_URL") or RUNTIME_CONFIG.get("erp_base_url") or None)  # type: ignore[assignment]
    internal_api_key: str = (os.getenv("INTERNAL_API_KEY") or "").strip()
    allowed_origins: tuple[str, ...] = (
        "http://127.0.0.1:8887",
        "http://localhost:8887",
        "http://127.0.0.1:8888",
        "http://localhost:8888",
        "http://127.0.0.1:8890",
        "http://localhost:8890",
    )


settings = Settings()


# ── 模型路由表 ──────────────────────────────────────────────────
# 每個任務可指向不同的 Ollama 模型和超時設定。
# 優先級：環境變數 > runtime_config.json > 預設值

DEFAULT_MODEL_ROUTING: dict[str, dict] = {
    "spc_analyze":       {"model": "qwen3:1.7b",   "timeout": 30},
    "doc_audit":         {"model": "gemma3:4b",     "timeout": 60},
    "deviation_analyze": {"model": "gemma3:4b",     "timeout": 60},
    "knowledge_qa":      {"model": "gemma4:latest", "timeout": 300},
    "doc_compare":       {"model": "gemma4:latest", "timeout": 300},
    "chat":              {"model": "gemma4:latest", "timeout": 300},
    "rag_chat":          {"model": "gemma4:latest", "timeout": 300},
}


def load_model_routing() -> dict[str, dict]:
    import copy
    routing = copy.deepcopy(DEFAULT_MODEL_ROUTING)
    rt_routing = RUNTIME_CONFIG.get("model_routing", {})
    for task, overrides in rt_routing.items():
        if task in routing:
            routing[task].update(overrides)
    for task in routing:
        env_model = os.getenv(f"OLLAMA_MODEL_{task.upper()}")
        if env_model:
            routing[task]["model"] = env_model.strip()
        env_timeout = os.getenv(f"OLLAMA_TIMEOUT_{task.upper()}")
        if env_timeout:
            routing[task]["timeout"] = int(env_timeout)
    return routing


MODEL_ROUTING = load_model_routing()

_installed_model_names: list[str] | None = None


def get_installed_model_names() -> list[str]:
    global _installed_model_names
    if _installed_model_names is None:
        try:
            import httpx
            with httpx.Client(timeout=5) as c:
                r = c.get(f"{settings.ollama_base_url.rstrip('/')}/api/tags")
                _installed_model_names = [m["name"] for m in r.json().get("models", [])]
        except Exception:
            _installed_model_names = []
    return _installed_model_names


def resolve_model_for_task(task_type: str | None = None, model_override: str | None = None) -> tuple[str, int]:
    if model_override:
        for cfg in MODEL_ROUTING.values():
            if cfg["model"] == model_override:
                return model_override, cfg["timeout"]
        return model_override, settings.ollama_timeout
    if task_type and task_type in MODEL_ROUTING:
        model = MODEL_ROUTING[task_type]["model"]
        timeout = MODEL_ROUTING[task_type]["timeout"]
        installed = get_installed_model_names()
        if installed and model not in installed:
            model = settings.ollama_model
            timeout = settings.ollama_timeout
        return model, timeout
    return settings.ollama_model, settings.ollama_timeout
