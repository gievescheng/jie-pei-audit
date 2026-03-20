from __future__ import annotations

import uvicorn

from runtime_paths import migrate_legacy_private_files, public_root_contains_private_files
from v2_backend.app.config import settings


if __name__ == "__main__":
    migrated = migrate_legacy_private_files()
    for item in migrated:
        print(f"[security-info] migrated private file: {item}")
    if public_root_contains_private_files():
        print("[security-warning] private config files are still present in the project root.")
    if settings.database_policy != "dev":
        print(f"[db-policy] {settings.database_policy} mode: PostgreSQL failure will stop V2 instead of falling back to SQLite.")
    uvicorn.run("v2_backend.app.main:app", host=settings.host, port=settings.port, reload=False)
