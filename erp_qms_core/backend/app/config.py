from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = BACKEND_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_DB = DATA_DIR / "erp_qms_core.db"


@dataclass(frozen=True)
class Settings:
    app_name: str = "jepe-erp-qms-core"
    host: str = os.getenv("ERP_QMS_CORE_HOST", "127.0.0.1")
    port: int = int(os.getenv("ERP_QMS_CORE_PORT", "8895"))
    database_url: str = os.getenv(
        "ERP_QMS_CORE_DATABASE_URL",
        f"sqlite:///{DEFAULT_DB.as_posix()}",
    )
    jwt_secret: str = os.getenv(
        "ERP_QMS_CORE_JWT_SECRET",
        "請務必在正式環境修改此密鑰 CHANGE ME IN PRODUCTION MIN 32 CHARS!!",
    )
    jwt_algorithm: str = os.getenv("ERP_QMS_CORE_JWT_ALGO", "HS256")
    # 服務間內部溝通金鑰（v2_backend 呼叫 ERP 內部端點時使用）
    # 正式環境請設定環境變數 ERP_QMS_CORE_SERVICE_KEY
    internal_service_key: str = os.getenv(
        "ERP_QMS_CORE_SERVICE_KEY",
        "jepe-internal-service-key-dev-change-in-prod",
    )
    allowed_origins: tuple = tuple(
        os.getenv(
            "ERP_QMS_CORE_ALLOWED_ORIGINS",
            "http://127.0.0.1:8895,http://localhost:8895,"
            "http://127.0.0.1:8888,http://localhost:8888,"
            "http://127.0.0.1:3000,http://localhost:3000",
        ).split(",")
    )


settings = Settings()
