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


settings = Settings()
