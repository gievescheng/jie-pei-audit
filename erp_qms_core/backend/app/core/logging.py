from __future__ import annotations

import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    """設定整個應用程式的 logging 格式與等級。
    在 main.py lifespan 或 startup 時呼叫一次即可。
    """
    numeric = getattr(logging, level.upper(), logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    root = logging.getLogger()
    root.setLevel(numeric)
    if not root.handlers:
        root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """取得具名 logger，供各模組使用。"""
    return logging.getLogger(name)
