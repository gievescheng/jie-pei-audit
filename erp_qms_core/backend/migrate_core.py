from __future__ import annotations

from pathlib import Path


def main() -> int:
    try:
        from alembic import command
        from alembic.config import Config
    except Exception as exc:
        raise SystemExit("Alembic is not installed. Run: py -3.13 -m pip install -r requirements.txt") from exc

    config = Config(str(Path(__file__).resolve().parent / "alembic.ini"))
    command.upgrade(config, "head")
    print("migration_complete=head")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
