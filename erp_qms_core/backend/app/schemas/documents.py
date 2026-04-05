from __future__ import annotations

from pydantic import BaseModel


class QmsDocumentCreate(BaseModel):
    doc_no: str
    doc_name: str
    doc_type: str = "管理程序"
    version: str = "1.0"
    department: str = ""
    author: str = ""
    issue_date: str = ""          # "YYYY-MM-DD"
    retention_years: int = 16
    pdf_path: str = ""
    docx_path: str = ""
    remarks: str = ""


class QmsDocumentUpdate(BaseModel):
    doc_name: str | None = None
    doc_type: str | None = None
    version: str | None = None
    department: str | None = None
    author: str | None = None
    issue_date: str | None = None
    retention_years: int | None = None
    pdf_path: str | None = None
    docx_path: str | None = None
    remarks: str | None = None
