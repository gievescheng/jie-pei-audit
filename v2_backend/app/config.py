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
    host: str = os.getenv("V2_HOST") or str(RUNTIME_CONFIG.get("host") or "127.0.0.1")
    port: int = int(os.getenv("V2_PORT") or str(RUNTIME_CONFIG.get("port") or "8890"))
    # ERP 核心系統連線設定（用於讀取產品、客戶、工單等主資料）
    erp_base_url: str = os.getenv("ERP_BASE_URL", "http://127.0.0.1:8895")
    erp_service_key: str = os.getenv("ERP_SERVICE_KEY", "jepe-internal-service-key-dev-change-in-prod")
    erp_timeout: int = int(os.getenv("ERP_TIMEOUT", "10"))
    # Email / SMTP 設定（通知提醒發送用）
    smtp_host: str = os.getenv("SMTP_HOST", "")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_user: str = os.getenv("SMTP_USER", "")
    smtp_pass: str = os.getenv("SMTP_PASS", "")
    smtp_from: str = os.getenv("SMTP_FROM", "")
    allowed_origins: tuple[str, ...] = (
        "http://127.0.0.1:8888",
        "http://localhost:8888",
        "http://127.0.0.1:8890",
        "http://localhost:8890",
    )


settings = Settings()
