from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    try:
        from alembic import command
        from alembic.config import Config
    except Exception as exc:
        raise SystemExit(
            "Alembic is not installed. Run: py -3.13 -m pip install -r v2_backend/requirements-v2.txt"
        ) from exc

    parser = argparse.ArgumentParser(description="Run V2 database migrations.")
    parser.add_argument("--revision", default="head", help="Revision to upgrade to. Default: head")
    parser.add_argument("--stamp-head", action="store_true", help="Mark the current database as already matching head without creating tables.")
    args = parser.parse_args()

    config = Config(str(Path(__file__).resolve().parent / "alembic.ini"))
    if args.stamp_head:
        command.stamp(config, args.revision)
        print(f"migration_stamped={args.revision}")
        return 0

    command.upgrade(config, args.revision)
    print(f"migration_complete={args.revision}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
