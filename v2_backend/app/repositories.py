from __future__ import annotations

import json
import re

from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from . import models


QUESTION_FILLERS = [
    "請問",
    "什麼",
    "要求",
    "如何",
    "是否",
    "哪些",
    "有無",
    "對",
    "與",
    "和",
    "及",
    "的",
    "嗎",
    "呢",
    "有沒有",
    "可以",
    "需要",
    "應該",
    "整個",
    "目前",
    "請",
    "告訴我",
    "說明",
    "介紹",
]


def build_search_terms(query: str) -> list[str]:
    cleaned = query
    for token in QUESTION_FILLERS:
        cleaned = cleaned.replace(token, " ")
    cleaned = re.sub(r"[^\w\u4e00-\u9fff]+", " ", cleaned)

    terms: list[str] = []
    seen: set[str] = set()

    def _add(t: str) -> None:
        t = t.strip()
        if len(t) >= 2 and t not in seen:
            seen.add(t)
            terms.append(t)

    for part in cleaned.split():
        _add(part)
        # For Chinese segments generate 4-char and 2-char n-grams so
        # near-synonyms (評選/評鑑) still share partial overlap
        if re.search(r"[\u4e00-\u9fff]", part) and len(part) >= 4:
            for n in (4, 3, 2):
                for i in range(len(part) - n + 1):
                    _add(part[i : i + n])

    # Also try the raw query stripped of spaces as one big term
    raw = re.sub(r"\s+", "", query)
    _add(raw)

    return terms[:20]



def get_document_by_id(session: Session, document_id: str):
    return session.get(models.Document, document_id)



def get_document_by_path(session: Session, source_path: str):
    stmt = select(models.Document).where(models.Document.source_path == source_path)
    return session.execute(stmt).scalar_one_or_none()



def replace_document(
    session: Session,
    *,
    source_path: str,
    title: str,
    document_code: str,
    file_type: str,
    version: str,
    owner_dept: str,
    source_system: str,
    full_text: str,
    chunks: list[dict],
):
    document = get_document_by_path(session, source_path)
    if document:
        session.execute(delete(models.DocumentChunk).where(models.DocumentChunk.document_id == document.id))
        document.title = title
        document.document_code = document_code
        document.file_type = file_type
        document.version = version
        document.owner_dept = owner_dept
        document.source_system = source_system
        document.full_text = full_text
    else:
        document = models.Document(
            source_path=source_path,
            title=title,
            document_code=document_code,
            file_type=file_type,
            version=version,
            owner_dept=owner_dept,
            source_system=source_system,
            full_text=full_text,
        )
        session.add(document)
        session.flush()

    for index, chunk in enumerate(chunks):
        session.add(
            models.DocumentChunk(
                document_id=document.id,
                chunk_index=index,
                page_no=chunk.get("page_no"),
                section_name=chunk.get("section_name", ""),
                content=chunk.get("content", ""),
            )
        )
    session.flush()
    return document



def search_chunks(session: Session, query: str, limit: int = 8, document_ids: list[str] | None = None):
    terms = build_search_terms(query)
    stmt = select(models.DocumentChunk, models.Document.title, models.Document.source_path).join(models.Document)
    if document_ids:
        stmt = stmt.where(models.DocumentChunk.document_id.in_(document_ids))
    if terms:
        clauses = [models.DocumentChunk.content.ilike(f"%{term}%") for term in terms]
        stmt = stmt.where(or_(*clauses))
    rows = session.execute(stmt.limit(limit * 6)).all()
    results = []
    seen_chunks: set[str] = set()
    for chunk, title, source_path in rows:
        if chunk.id in seen_chunks:
            continue
        seen_chunks.add(chunk.id)
        content_lower = chunk.content.lower()
        # Weight longer matching terms higher to prefer specific matches
        score = sum(
            content_lower.count(term.lower()) * len(term)
            for term in terms
        ) if terms else 1
        results.append(
            {
                "document_id": chunk.document_id,
                "title": title,
                "source_path": source_path,
                "chunk_id": chunk.id,
                "chunk_index": chunk.chunk_index,
                "page_no": chunk.page_no,
                "section_name": chunk.section_name,
                "content": chunk.content,
                "score": score,
            }
        )
    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:limit]



def upsert_prompt_template(
    session: Session,
    *,
    template_code: str,
    template_name: str,
    task_type: str,
    version: str,
    system_prompt: str,
    policy_prompt: str,
    user_prompt_template: str,
    output_schema: str,
):
    template = session.execute(select(models.PromptTemplate).where(models.PromptTemplate.template_code == template_code)).scalar_one_or_none()
    if template is None:
        template = models.PromptTemplate(template_code=template_code, template_name=template_name, task_type=task_type)
        session.add(template)
        session.flush()

    versions = session.execute(select(models.PromptTemplateVersion).where(models.PromptTemplateVersion.template_id == template.id)).scalars().all()
    for item in versions:
        item.is_active = False
        if item.status == "released":
            item.status = "deprecated"

    version_ref = models.PromptTemplateVersion(
        template_id=template.id,
        version=version,
        status="released",
        system_prompt=system_prompt,
        policy_prompt=policy_prompt,
        user_prompt_template=user_prompt_template,
        output_schema=output_schema,
        is_active=True,
    )
    session.add(version_ref)
    session.flush()
    session.add(models.PromptTemplateReleaseLog(version_id=version_ref.id, action="seed_release", note="initial seed", actor="system"))
    return template, version_ref



def get_active_prompt_version(session: Session, task_type: str):
    stmt = (
        select(models.PromptTemplateVersion, models.PromptTemplate)
        .join(models.PromptTemplate)
        .where(models.PromptTemplate.task_type == task_type)
        .where(models.PromptTemplateVersion.is_active.is_(True))
        .where(models.PromptTemplateVersion.status == "released")
        .limit(1)
    )
    return session.execute(stmt).first()



def create_audit_log(
    session: Session,
    *,
    trace_id: str,
    task_type: str,
    user_id: str,
    prompt_version: str,
    result_status: str,
    request_summary: str,
):
    item = models.AuditLog(
        trace_id=trace_id,
        task_type=task_type,
        user_id=user_id,
        prompt_version=prompt_version,
        result_status=result_status,
        request_summary=request_summary,
    )
    session.add(item)
    session.flush()
    return item



def get_compare_cache_by_key(session: Session, cache_key: str):
    stmt = select(models.CompareCache).where(models.CompareCache.cache_key == cache_key).limit(1)
    return session.execute(stmt).scalar_one_or_none()


def upsert_compare_cache(
    session: Session,
    *,
    cache_key: str,
    left_document_id: str,
    right_document_id: str,
    use_llm: bool,
    response_data: dict,
):
    item = get_compare_cache_by_key(session, cache_key)
    payload = json.dumps(response_data, ensure_ascii=False)
    if item is None:
        item = models.CompareCache(
            cache_key=cache_key,
            left_document_id=left_document_id,
            right_document_id=right_document_id,
            use_llm=use_llm,
            response_json=payload,
        )
        session.add(item)
    else:
        item.left_document_id = left_document_id
        item.right_document_id = right_document_id
        item.use_llm = use_llm
        item.response_json = payload
    session.flush()
    return item


def get_audit_cache_by_key(session: Session, cache_key: str):
    stmt = select(models.AuditCache).where(models.AuditCache.cache_key == cache_key).limit(1)
    return session.execute(stmt).scalar_one_or_none()


def upsert_audit_cache(
    session: Session,
    *,
    cache_key: str,
    document_id: str,
    llm_enabled: bool,
    response_data: dict,
):
    item = get_audit_cache_by_key(session, cache_key)
    payload = json.dumps(response_data, ensure_ascii=False)
    if item is None:
        item = models.AuditCache(
            cache_key=cache_key,
            document_id=document_id,
            llm_enabled=llm_enabled,
            response_json=payload,
        )
        session.add(item)
    else:
        item.document_id = document_id
        item.llm_enabled = llm_enabled
        item.response_json = payload
    session.flush()
    return item


def get_cache_status(session: Session) -> dict:
    compare_count = session.execute(select(func.count()).select_from(models.CompareCache)).scalar_one()
    audit_count = session.execute(select(func.count()).select_from(models.AuditCache)).scalar_one()
    latest_compare = session.execute(
        select(models.CompareCache).order_by(models.CompareCache.created_at.desc()).limit(1)
    ).scalar_one_or_none()
    latest_audit = session.execute(
        select(models.AuditCache).order_by(models.AuditCache.created_at.desc()).limit(1)
    ).scalar_one_or_none()
    return {
        "compare_cache_count": int(compare_count or 0),
        "audit_cache_count": int(audit_count or 0),
        "latest_compare_cache_at": latest_compare.created_at.isoformat() if latest_compare else "",
        "latest_audit_cache_at": latest_audit.created_at.isoformat() if latest_audit else "",
    }


def clear_cache(session: Session, target: str = "all") -> dict:
    targets = {"all", "compare", "audit"}
    if target not in targets:
        raise ValueError(f"Unsupported cache target: {target}")
    deleted_compare = 0
    deleted_audit = 0
    if target in {"all", "compare"}:
        deleted_compare = session.execute(delete(models.CompareCache)).rowcount or 0
    if target in {"all", "audit"}:
        deleted_audit = session.execute(delete(models.AuditCache)).rowcount or 0
    session.flush()
    return {
        "target": target,
        "deleted_compare_cache": int(deleted_compare),
        "deleted_audit_cache": int(deleted_audit),
    }


def save_compare_result(
    session: Session,
    *,
    left_document_id: str | None,
    right_document_id: str | None,
    left_title: str,
    right_title: str,
    similarity: float,
    added_count: int,
    removed_count: int,
    conclusion_json: str,
    created_by: str = "system",
):
    item = models.CompareResult(
        left_document_id=left_document_id,
        right_document_id=right_document_id,
        left_title=left_title,
        right_title=right_title,
        similarity=similarity,
        added_count=added_count,
        removed_count=removed_count,
        conclusion_json=conclusion_json,
        created_by=created_by,
    )
    session.add(item)
    session.flush()
    return item


def list_compare_results(session: Session, *, limit: int = 20, offset: int = 0):
    stmt = (
        select(models.CompareResult)
        .order_by(models.CompareResult.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return session.execute(stmt).scalars().all()


def list_audit_logs(session: Session, *, task_types: list[str] | None = None, query: str = "", limit: int = 20):
    stmt = select(models.AuditLog).order_by(models.AuditLog.created_at.desc())
    if task_types:
        stmt = stmt.where(models.AuditLog.task_type.in_(task_types))
    if query.strip():
        like = f"%{query.strip()}%"
        stmt = stmt.where(
            or_(
                models.AuditLog.task_type.ilike(like),
                models.AuditLog.request_summary.ilike(like),
                models.AuditLog.prompt_version.ilike(like),
            )
        )
    return session.execute(stmt.limit(limit)).scalars().all()
