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


settings = _Settings()
