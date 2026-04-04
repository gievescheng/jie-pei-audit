from __future__ import annotations

import os
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[2]  # erp_qms_core/backend
DATA_DIR = BACKEND_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_DB = DATA_DIR / "erp_qms_core.db"


class _Settings:
    """Lazy settings: always reads from current env vars so tests can override."""

    @property
    def app_name(self) -> str:
        return "jepe-erp-qms-core"

    @property
    def host(self) -> str:
        return os.getenv("ERP_QMS_CORE_HOST", "127.0.0.1")

    @property
    def port(self) -> int:
        return int(os.getenv("ERP_QMS_CORE_PORT", "8895"))

    @property
    def database_url(self) -> str:
        return os.getenv(
            "ERP_QMS_CORE_DATABASE_URL",
            f"sqlite:///{DEFAULT_DB.as_posix()}",
        )

    @property
    def jwt_secret(self) -> str:
        secret = os.getenv("ERP_QMS_CORE_JWT_SECRET", "")
        if not secret:
            raise RuntimeError(
                "ERP_QMS_CORE_JWT_SECRET 未設定。"
                " 請在 .env 或環境變數中設定一個隨機字串（至少 32 字元）。"
            )
        return secret

    @property
    def token_expire_minutes(self) -> int:
        return int(os.getenv("ERP_QMS_CORE_TOKEN_EXPIRE_MINUTES", "480"))  # 預設 8 小時


settings = _Settings()
