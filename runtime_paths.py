from __future__ import annotations

import os
import secrets
import shutil
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
PRIVATE_CONFIG_DIR = Path(
    os.getenv("AUTO_AUDIT_CONFIG_DIR")
    or (Path(os.getenv("APPDATA") or str(PROJECT_ROOT)) / "AutoAudit")
).resolve()
PRIVATE_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
PRIVATE_DATA_DIR = (PRIVATE_CONFIG_DIR / "data").resolve()
PRIVATE_DATA_DIR.mkdir(parents=True, exist_ok=True)

LOG_DIR = (PRIVATE_CONFIG_DIR / "logs").resolve()
LOG_DIR.mkdir(parents=True, exist_ok=True)

V2_RUNTIME_CONFIG_PATH = PRIVATE_CONFIG_DIR / "v2_runtime.json"
GOOGLE_CONFIG_PATH = PRIVATE_CONFIG_DIR / "google_calendar_config.json"
GOOGLE_TOKEN_PATH = PRIVATE_CONFIG_DIR / "google_calendar_tokens.json"
FLASK_SECRET_PATH = PRIVATE_CONFIG_DIR / "flask_secret.key"

LEGACY_PRIVATE_FILES = {
    PROJECT_ROOT / ".v2_runtime.json": V2_RUNTIME_CONFIG_PATH,
    PROJECT_ROOT / ".google_calendar_config.json": GOOGLE_CONFIG_PATH,
    PROJECT_ROOT / ".google_calendar_tokens.json": GOOGLE_TOKEN_PATH,
    PROJECT_ROOT / ".flask_secret.key": FLASK_SECRET_PATH,
}


def migrate_legacy_private_files() -> list[str]:
    migrated = []
    for legacy_path, target_path in LEGACY_PRIVATE_FILES.items():
        if not legacy_path.exists():
            continue
        if target_path.exists():
            try:
                legacy_path.unlink()
            except OSError:
                pass
            continue
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(legacy_path), str(target_path))
        migrated.append(f"{legacy_path.name} -> {target_path}")
    return migrated


def get_or_create_flask_secret() -> str:
    if FLASK_SECRET_PATH.exists():
        value = FLASK_SECRET_PATH.read_text(encoding="utf-8").strip()
        if value:
            return value
    value = secrets.token_urlsafe(48)
    FLASK_SECRET_PATH.write_text(value, encoding="utf-8")
    return value


def public_root_contains_private_files() -> list[Path]:
    return [legacy_path for legacy_path in LEGACY_PRIVATE_FILES if legacy_path.exists()]
