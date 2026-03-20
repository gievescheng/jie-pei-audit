from __future__ import annotations

import csv
from pathlib import Path

import httpx
from docx import Document as DocxDocument
from openpyxl import load_workbook
from pypdf import PdfReader

from .config import settings


def resolve_project_path(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    return (settings.project_root / path_str).resolve()


def parse_document(path_str: str) -> dict:
    path = resolve_project_path(path_str)
    suffix = path.suffix.lower()
    if not path.exists():
        raise FileNotFoundError(f"Document not found: {path_str}")

    if suffix == ".docx":
        return _parse_docx(path)
    if suffix == ".pdf":
        return _parse_pdf(path)
    if suffix in {".xlsx", ".xlsm"}:
        return _parse_xlsx(path)
    if suffix == ".csv":
        return _parse_csv(path)
    if suffix in {".txt", ".md"}:
        return _parse_text(path)
    raise ValueError(f"Unsupported document type: {suffix}")


def _chunk_lines(lines: list[str], *, page_no: int | None = None) -> list[dict]:
    chunks = []
    buffer = []
    current_len = 0
    for line in lines:
        cleaned = line.strip()
        if not cleaned:
            continue
        if current_len + len(cleaned) > 800 and buffer:
            text = "\n".join(buffer)
            chunks.append({"page_no": page_no, "section_name": text.splitlines()[0][:80], "content": text})
            buffer = []
            current_len = 0
        buffer.append(cleaned)
        current_len += len(cleaned)
    if buffer:
        text = "\n".join(buffer)
        chunks.append({"page_no": page_no, "section_name": text.splitlines()[0][:80], "content": text})
    return chunks


def _parse_docx(path: Path) -> dict:
    doc = DocxDocument(path)
    lines = [paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()]
    return {"title": path.stem, "file_type": "docx", "full_text": "\n".join(lines), "chunks": _chunk_lines(lines)}


def _parse_pdf(path: Path) -> dict:
    reader = PdfReader(str(path))
    chunks = []
    pages_text = []
    for idx, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            pages_text.append(text)
            chunks.extend(_chunk_lines(text.splitlines(), page_no=idx))
    return {"title": path.stem, "file_type": "pdf", "full_text": "\n\n".join(pages_text), "chunks": chunks}


def _parse_xlsx(path: Path) -> dict:
    wb = load_workbook(path, data_only=True)
    lines = []
    for sheet in wb.worksheets:
        lines.append(f"[Sheet] {sheet.title}")
        for row in sheet.iter_rows(values_only=True):
            values = [str(cell).strip() for cell in row if cell not in (None, "")]
            if values:
                lines.append(" | ".join(values))
    return {"title": path.stem, "file_type": "xlsx", "full_text": "\n".join(lines), "chunks": _chunk_lines(lines)}


def _parse_csv(path: Path) -> dict:
    lines = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        for row in reader:
            values = [str(cell).strip() for cell in row if str(cell).strip()]
            if values:
                lines.append(" | ".join(values))
    return {"title": path.stem, "file_type": "csv", "full_text": "\n".join(lines), "chunks": _chunk_lines(lines)}


def _parse_text(path: Path) -> dict:
    text = path.read_text(encoding="utf-8-sig")
    return {"title": path.stem, "file_type": path.suffix.lower().lstrip("."), "full_text": text, "chunks": _chunk_lines(text.splitlines())}


def maybe_call_openrouter(*, system_prompt: str, policy_prompt: str, user_prompt: str) -> str | None:
    if not settings.openrouter_api_key:
        return None
    payload = {
        "model": settings.openrouter_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": policy_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 900,
    }
    with httpx.Client(timeout=settings.openrouter_timeout) as client:
        response = client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()
        body = response.json()
        choices = body.get("choices") or []
        if not choices:
            return None
        return (((choices[0] or {}).get("message") or {}).get("content") or "").strip() or None
