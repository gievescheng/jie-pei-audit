"""
pdf_structured_parser.py
========================
封裝 opendataloader-pdf 的輕量 adapter。

對外介面：
    extract_pdf_text(path)      → str   純文字（適合欄位映射）
    extract_pdf_markdown(path)  → str   Markdown（適合 RAG / 文件稽核）
    is_available()              → bool  環境是否支援（Java + 套件）

設計原則（依照 OpenDataLoader_PDF_PoC_整合方案.md）：
- 只負責「抽取」，不做欄位判定
- 若失敗則拋 PdfExtractionError，由呼叫端決定是否 fallback
- 每次呼叫都在獨立 temp dir 執行，避免檔案衝突
"""

from __future__ import annotations

import logging
import shutil
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


class PdfExtractionError(Exception):
    """opendataloader-pdf 解析失敗時拋出。"""


def is_available() -> bool:
    """回傳 True 表示 Java + opendataloader-pdf 套件均可使用。"""
    # 確認套件可 import
    try:
        import opendataloader_pdf  # noqa: F401
    except ImportError:
        return False
    # 確認 Java 存在
    return shutil.which("java") is not None


def _run_convert(path: Path, fmt: str) -> str:
    """
    內部：執行 opendataloader-pdf 轉換，回傳指定格式的輸出文字。
    fmt 可為 "text" 或 "markdown"。
    """
    import opendataloader_pdf  # 延遲 import，讓主程式不依賴此套件啟動

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            opendataloader_pdf.convert(
                input_path=str(path),
                output_dir=tmpdir,
                format=fmt,
                quiet=True,
            )
        except Exception as exc:
            raise PdfExtractionError(f"opendataloader-pdf 轉換失敗：{exc}") from exc

        ext = ".txt" if fmt == "text" else ".md"
        out_files = list(Path(tmpdir).glob(f"*{ext}"))
        if not out_files:
            raise PdfExtractionError(f"opendataloader-pdf 未產生 {ext} 輸出")

        return out_files[0].read_text(encoding="utf-8", errors="replace")


def extract_pdf_text(path: Path | str) -> str:
    """
    將 PDF 轉為純文字字串（適合欄位映射 / keyword 抽取）。
    空白行會被壓縮，以利後續 regex 處理。

    Raises:
        PdfExtractionError: 轉換失敗。
    """
    raw = _run_convert(Path(path), "text")
    # 壓縮連續空行（保留單一換行以維持段落分隔）
    lines = raw.splitlines()
    cleaned: list[str] = []
    blank_run = 0
    for line in lines:
        if line.strip():
            blank_run = 0
            cleaned.append(line)
        else:
            blank_run += 1
            if blank_run == 1:
                cleaned.append("")   # 保留一個空行作為段落分隔
    return "\n".join(cleaned)


def extract_pdf_markdown(path: Path | str) -> str:
    """
    將 PDF 轉為 Markdown（適合 RAG / 文件稽核 / AI 工作台）。

    Raises:
        PdfExtractionError: 轉換失敗。
    """
    return _run_convert(Path(path), "markdown")
