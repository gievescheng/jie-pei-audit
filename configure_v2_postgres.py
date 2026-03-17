from __future__ import annotations

import argparse
import json
from pathlib import Path

from sqlalchemy import create_engine, text

from v2_backend.app.config import RUNTIME_CONFIG_PATH
from v2_backend.app.db import mask_database_url


def load_runtime_config() -> dict:
    if not RUNTIME_CONFIG_PATH.exists():
        return {}
    return json.loads(RUNTIME_CONFIG_PATH.read_text(encoding="utf-8-sig"))


def save_runtime_config(data: dict) -> None:
    RUNTIME_CONFIG_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def detect_driver() -> str | None:
    for module_name, driver_name in (("psycopg", "psycopg"), ("psycopg2", "psycopg2"), ("pg8000", "pg8000")):
        try:
            __import__(module_name)
            return driver_name
        except Exception:
            continue
    return None


def normalize_postgres_url(url: str) -> str:
    value = url.strip()
    if value.startswith("postgres://"):
        value = "postgresql://" + value[len("postgres://") :]
    if value.startswith("postgresql://") and "+" not in value.split("://", 1)[0]:
        driver = detect_driver()
        if not driver:
            raise RuntimeError("No PostgreSQL driver is installed. Install psycopg, psycopg2, or pg8000 first.")
        value = value.replace("postgresql://", f"postgresql+{driver}://", 1)
    if not value.startswith("postgresql+"):
        raise RuntimeError("Database URL must start with postgresql:// or postgresql+driver://")
    return value


def test_connection(database_url: str) -> None:
    engine = create_engine(database_url, future=True, pool_pre_ping=True)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Configure Auto Audit V2 to use PostgreSQL.")
    parser.add_argument("--url", required=True, help="PostgreSQL connection URL.")
    parser.add_argument("--write-config", action="store_true", help="Persist the normalized URL to .v2_runtime.json.")
    parser.add_argument("--test-only", action="store_true", help="Only test the connection, do not write config.")
    parser.add_argument("--policy", choices=["dev", "prod"], default="prod", help="Database fallback policy. Use prod to disable silent SQLite fallback.")
    args = parser.parse_args()

    database_url = normalize_postgres_url(args.url)
    test_connection(database_url)
    print("connection_ok=" + mask_database_url(database_url))

    if args.write_config and not args.test_only:
        config = load_runtime_config()
        config["database_url"] = database_url
        config["database_policy"] = args.policy
        save_runtime_config(config)
        print("config_written=" + str(RUNTIME_CONFIG_PATH))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
