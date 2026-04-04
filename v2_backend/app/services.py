from __future__ import annotations

import difflib
import hashlib
import json
import re
from pathlib import Path

from . import adapters, engines, repositories
from .prompt_seed import SEED_TEMPLATES


SUPPORTED_VERSION_EXTENSIONS = {".docx", ".doc", ".pdf", ".xlsx", ".xlsm", ".csv", ".txt", ".md"}


def _normalize_version_key(value: str) -> str:
    text = value or ""
    text = re.sub(r"~\$", "", text)
    text = re.sub(r"\b(v|ver|version)\s*[\d.]+\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"[\(（]?\s*[\d]+(?:\.[\d]+)*\s*[\)）]?", " ", text)
    text = re.sub(r"(正式版|修訂版|最新版|最終版)", " ", text)
    text = re.sub(r"[_\-\s]+", "", text)
    text = re.sub(r"[^\w\u4e00-\u9fff]+", "", text)
    return text.lower()


def _build_version_candidate(base_path: Path, candidate_path: Path) -> dict | None:
    if candidate_path == base_path:
        return None
    if candidate_path.name.startswith("~$"):
        return None
    if candidate_path.suffix.lower() not in SUPPORTED_VERSION_EXTENSIONS:
        return None

    base_key = _normalize_version_key(base_path.stem)
    candidate_key = _normalize_version_key(candidate_path.stem)
    if not base_key or not candidate_key:
        return None

    ratio = difflib.SequenceMatcher(None, base_key, candidate_key).ratio()
    same_stem_family = base_key == candidate_key
    if not same_stem_family and ratio < 0.62:
        return None

    version_match = re.search(r"([\d]+(?:\.[\d]+)*)", candidate_path.stem)
    version_label = version_match.group(1) if version_match else ""
    return {
        "path": str(candidate_path),
        "title": candidate_path.stem,
        "version_label": version_label,
        "same_family": same_stem_family,
        "similarity": round(ratio, 4),
        "extension": candidate_path.suffix.lower(),
    }


def _extract_version_label(document: dict | object) -> str:
    if isinstance(document, dict):
        version = str(document.get("version") or "").strip()
        title = str(document.get("title") or "")
        source_path = str(document.get("source_path") or "")
    else:
        version = str(getattr(document, "version", "") or "").strip()
        title = str(getattr(document, "title", "") or "")
        source_path = str(getattr(document, "source_path", "") or "")
    if version:
        return version
    for text in (title, source_path):
        match = re.search(r"([\d]+(?:\.[\d]+)*)", text)
        if match:
            return match.group(1)
    return ""


def _build_version_change_conclusion(left_doc, right_doc, similarity: float, added_count: int, removed_count: int, left_issue_count: int, right_issue_count: int) -> dict:
    left_key = _normalize_version_key(left_doc.title)
    right_key = _normalize_version_key(right_doc.title)
    same_family = bool(left_key and right_key and left_key == right_key)
    left_version = _extract_version_label(left_doc)
    right_version = _extract_version_label(right_doc)

    if same_family:
        conclusion = (
            f"判定為同文件版次差異。左側版次 {left_version or '未標示'}，右側版次 {right_version or '未標示'}；"
            f"文字相似度 {similarity}，右側新增 {added_count} 項，左側移除 {removed_count} 項，"
            f"左側獨有缺口 {left_issue_count} 項，右側獨有缺口 {right_issue_count} 項。"
        )
        recommendation = "建議以右側文件作為新版候選，並逐項覆核新增與移除內容。"
    else:
        conclusion = (
            f"目前比對對象較可能屬於不同文件或不同程序類型。文字相似度 {similarity}，"
            f"右側新增 {added_count} 項，左側移除 {removed_count} 項。"
        )
        recommendation = "建議先確認是否為同一文件族，再決定是否採用版次差異結論。"

    return {
        "same_document_family": same_family,
        "left_version_label": left_version,
        "right_version_label": right_version,
        "version_change_conclusion": conclusion,
        "version_change_recommendation": recommendation,
    }


def ensure_seed_prompts(session) -> None:
    for item in SEED_TEMPLATES:
        if repositories.get_active_prompt_version(session, item["task_type"]):
            continue
        repositories.upsert_prompt_template(session, **item)



def resolve_prompt(session, task_type: str) -> dict:
    row = repositories.get_active_prompt_version(session, task_type)
    if not row:
        raise ValueError(f"No active prompt version for task_type={task_type}")
    version_ref, template = row
    return {
        "template_code": template.template_code,
        "template_name": template.template_name,
        "task_type": template.task_type,
        "version": version_ref.version,
        "system_prompt": version_ref.system_prompt,
        "policy_prompt": version_ref.policy_prompt,
        "user_prompt_template": version_ref.user_prompt_template,
        "output_schema": version_ref.output_schema,
    }



def ingest_documents(session, request) -> dict:
    results = []
    failures = []
    for path_str in request.paths:
        try:
            parsed = adapters.parse_document(path_str)
            meta = request.metadata.get(path_str, {})
            document = repositories.replace_document(
                session,
                source_path=str(adapters.resolve_project_path(path_str)),
                title=meta.get("title") or parsed["title"],
                document_code=meta.get("document_code") or Path(path_str).stem,
                file_type=parsed["file_type"],
                version=meta.get("version", ""),
                owner_dept=meta.get("owner_dept", ""),
                source_system=meta.get("source_system", "local"),
                full_text=parsed["full_text"],
                chunks=parsed["chunks"],
            )
            results.append(
                {
                    "document_id": document.id,
                    "title": document.title,
                    "source_path": document.source_path,
                    "chunk_count": len(parsed["chunks"]),
                    "file_type": parsed["file_type"],
                }
            )
        except Exception as exc:
            failures.append({"path": path_str, "error": str(exc)})
    return {
        "ingested_count": len(results),
        "failed_count": len(failures),
        "documents": results,
        "failures": failures,
    }



def search_documents(session, query: str, limit: int = 8) -> dict:
    hits = repositories.search_chunks(session, query, limit=limit)
    return {
        "query": query,
        "hits": [
            {
                "document_id": hit["document_id"],
                "title": hit["title"],
                "source_path": hit["source_path"],
                "score": hit["score"],
                "preview": hit["content"][:220],
                "section_name": hit["section_name"],
                "page_no": hit["page_no"],
            }
            for hit in hits
        ],
    }


def get_runtime_cache_status(session) -> dict:
    return repositories.get_cache_status(session)


def clear_runtime_cache(session, target: str = "all") -> dict:
    result = repositories.clear_cache(session, target=target)
    result["remaining"] = repositories.get_cache_status(session)
    return result


def list_result_history(session, *, mode: str = "all", query: str = "", limit: int = 20) -> dict:
    task_map = {
        "all": ["doc_audit", "doc_audit_export_docx", "doc_compare", "doc_compare_export", "doc_compare_export_docx"],
        "audit": ["doc_audit"],
        "compare": ["doc_compare", "doc_compare_export", "doc_compare_export_docx"],
        "export": ["doc_audit_export_docx", "doc_compare_export", "doc_compare_export_docx"],
    }
    task_types = task_map.get(mode, task_map["all"])
    rows = repositories.list_audit_logs(session, task_types=task_types, query=query, limit=limit)
    items = []
    for row in rows:
        items.append(
            {
                "id": row.id,
                "trace_id": row.trace_id,
                "task_type": row.task_type,
                "prompt_version": row.prompt_version,
                "result_status": row.result_status,
                "request_summary": row.request_summary,
                "created_at": row.created_at.isoformat() if row.created_at else "",
            }
        )
    return {"mode": mode, "query": query, "items": items}


def suggest_version_candidates(session, request) -> dict:
    document = _load_or_ingest_single_document(session, request)
    if document is None:
        raise ValueError("Document not found. Provide document_id or path.")

    base_path = Path(document.source_path)
    search_dir = base_path.parent
    candidates = []
    seen = set()
    for candidate_path in search_dir.iterdir():
        if not candidate_path.is_file():
            continue
        candidate = _build_version_candidate(base_path, candidate_path)
        if candidate is None or candidate["path"] in seen:
            continue
        seen.add(candidate["path"])
        candidates.append(candidate)

    candidates.sort(key=lambda item: (0 if item["same_family"] else 1, -item["similarity"], item["path"]))
    limited = candidates[: request.limit]
    return {
        "base_document": {
            "document_id": document.id,
            "title": document.title,
            "source_path": document.source_path,
            "version": document.version,
        },
        "candidates": limited,
        "candidate_count": len(limited),
        "search_directory": str(search_dir),
    }



def _load_or_ingest_single_document(session, request):
    document = None
    if getattr(request, "document_id", None):
        document = repositories.get_document_by_id(session, request.document_id)
    elif getattr(request, "path", None):
        source_path = str(adapters.resolve_project_path(request.path))
        document = repositories.get_document_by_path(session, source_path)
        if document is None:
            ingest_documents(session, type("Tmp", (), {"paths": [request.path], "metadata": {}})())
            document = repositories.get_document_by_path(session, source_path)
    return document



def audit_document(session, request) -> dict:
    document = _load_or_ingest_single_document(session, request)
    if document is None:
        raise ValueError("Document not found. Provide document_id or path.")

    prompt = resolve_prompt(session, "doc_audit")
    llm_enabled = bool(adapters.settings.openrouter_api_key)
    audit_cache_payload = {
        "document_id": document.id,
        "document_updated_at": document.updated_at.isoformat() if getattr(document, "updated_at", None) else "",
        "prompt_version": prompt["version"],
        "llm_enabled": llm_enabled,
        "llm_model": adapters.settings.openrouter_model if llm_enabled else "",
    }
    audit_cache_key = hashlib.sha1(json.dumps(audit_cache_payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    audit_cache_entry = repositories.get_audit_cache_by_key(session, audit_cache_key)
    if audit_cache_entry:
        cached = json.loads(audit_cache_entry.response_json)
        cached.setdefault("document_title", document.title)
        cached.setdefault("document_path", document.source_path)
        cached["cache_hit"] = True
        return cached

    rule_result = engines.run_document_rules(document.full_text)
    citations = repositories.search_chunks(session, document.title, limit=5)

    if rule_result["issues"]:
        issue_titles = ", ".join(item["title"] for item in rule_result["issues"][:4])
        summary = f"文件 {document.title} 偵測到 {len(rule_result['issues'])} 項結構性缺口，主要問題包含：{issue_titles}。"
    else:
        summary = f"文件 {document.title} 已通過目前規則檢查，未偵測到必要章節缺漏，但仍建議人工覆核版面與簽核欄位。"

    llm_summary = adapters.call_llm(
        system_prompt=prompt["system_prompt"],
        policy_prompt=prompt["policy_prompt"],
        user_prompt=(
            prompt["user_prompt_template"]
            + "\n\nRule outputs:\n"
            + json.dumps(rule_result, ensure_ascii=False, indent=2)
            + "\n\nDocument title: "
            + document.title
        ),
        task_type="doc_audit",
    )
    if llm_summary:
        summary = llm_summary

    response_data = {
        "document_id": document.id,
        "document_title": document.title,
        "document_path": document.source_path,
        "summary": summary,
        "issues": rule_result["issues"],
        "insufficient_evidence": rule_result["insufficient_evidence"],
        "prompt_version": prompt["version"],
        "citations": [
            {
                "document_id": item["document_id"],
                "title": item["title"],
                "source_path": item["source_path"],
                "section_name": item["section_name"],
                "page_no": item["page_no"],
                "preview": item["content"][:180],
            }
            for item in citations
        ],
        "source_document_ids": [document.id],
        "tool_outputs_used": ["document_rule_engine"],
        "needs_human_review": True,
        "cache_hit": False,
    }
    repositories.upsert_audit_cache(
        session,
        cache_key=audit_cache_key,
        document_id=document.id,
        llm_enabled=llm_enabled,
        response_data=response_data,
    )
    return response_data



def analyze_spc(session, request) -> dict:
    """SPC 分析 — 使用 spc_engine.py 的完整實作（I-MR + Nelson Rules + Cpk CI）。"""
    from .spc_engine import run_imr

    prompt = resolve_prompt(session, "spc_analyze")
    values = engines.parse_numeric_values(request.values, request.csv_text)

    imr_result = run_imr(
        values=values,
        usl=request.usl,
        lsl=request.lsl,
        target=request.target,
        chart_id=request.parameter_name,
    )

    cap = imr_result.get("capability", {})
    metrics = {
        "count":             imr_result["n"],
        "mean":              imr_result["x_bar"],
        "stdev":             imr_result["sigma_mr"],
        "x_ucl":             imr_result["x_ucl"],
        "x_lcl":             imr_result["x_lcl"],
        "mr_ucl":            imr_result["mr_ucl"],
        "lsl":               request.lsl,
        "usl":               request.usl,
        "target":            request.target,
        "cp":                cap.get("cp"),
        "cpk":               cap.get("cpk"),
        "cpm":               cap.get("cpm"),
        "cpk_ci":            cap.get("cpk_ci"),
        "cpk_grade":         cap.get("grade"),
        "out_of_control_x":  imr_result["ooc_x"],
        "out_of_control_mr": imr_result["ooc_mr"],
        "nelson_signals":    imr_result["nelson_signals"],
        "warnings":          imr_result["warnings"],
        # build_spc_summaries 所需的相容鍵
        "trend": (
            "up" if len(values) >= 2 and values[-1] > values[0] else
            "down" if len(values) >= 2 and values[-1] < values[0] else "flat"
        ),
        "out_of_spec_count": sum(
            1 for v in values
            if (request.lsl is not None and v < request.lsl)
            or (request.usl is not None and v > request.usl)
        ),
    }
    abnormal_items = [
        {"index": i + 1, "value": v, "type": "ooc_x"}
        for i, v in enumerate(imr_result["x_values"])
        if i in imr_result["ooc_x"]
    ]

    engineering_summary, management_summary = engines.build_spc_summaries(
        request.parameter_name, metrics, abnormal_items
    )

    llm_summary = adapters.call_llm(
        system_prompt=prompt["system_prompt"],
        policy_prompt=prompt["policy_prompt"],
        user_prompt=(
            prompt["user_prompt_template"]
            + "\n\nMetrics:\n"
            + json.dumps(metrics, ensure_ascii=False, indent=2)
            + "\n\nNelson Signals:\n"
            + json.dumps(imr_result["nelson_signals"], ensure_ascii=False, indent=2)
        ),
        task_type="spc_analyze",
    )
    if llm_summary:
        management_summary = llm_summary

    return {
        "parameter_name":      request.parameter_name,
        "metrics":             metrics,
        "abnormal_items":      abnormal_items,
        "engineering_summary": engineering_summary,
        "management_summary":  management_summary,
        "prompt_version":      prompt["version"],
        "citations":           [],
        "source_document_ids": [],
        "tool_outputs_used":   ["spc_engine_v2"],
        "needs_human_review":  True,
    }



def draft_deviation(session, request) -> dict:
    prompt = resolve_prompt(session, "deviation_analyze")
    draft = engines.build_deviation_draft(request.issue_description, request.process_step, request.lot_no, request.severity)
    query = " ".join([request.issue_description, request.process_step, request.lot_no]).strip()
    citations = repositories.search_chunks(session, query, limit=5) if query else []

    llm_summary = adapters.call_llm(
        system_prompt=prompt["system_prompt"],
        policy_prompt=prompt["policy_prompt"],
        user_prompt=(
            prompt["user_prompt_template"]
            + "\n\nDraft:\n"
            + json.dumps(draft, ensure_ascii=False, indent=2)
            + "\n\nIssue:\n"
            + request.issue_description
        ),
        task_type="deviation_analyze",
    )
    draft["draft_summary"] = llm_summary or "此輸出為異常調查草稿，僅供人工覆核與轉入 CAPA/8D 前的整理依據。"

    return {
        **draft,
        "prompt_version": prompt["version"],
        "citations": [
            {
                "document_id": item["document_id"],
                "title": item["title"],
                "source_path": item["source_path"],
                "preview": item["content"][:180],
            }
            for item in citations
        ],
        "source_document_ids": list({item["document_id"] for item in citations}),
        "tool_outputs_used": ["deviation_rule_builder"],
        "needs_human_review": True,
    }



def answer_knowledge_question(session, request) -> dict:
    prompt = resolve_prompt(session, "knowledge_qa")
    scoped_document = _load_or_ingest_single_document(session, request) if (getattr(request, "document_id", None) or getattr(request, "path", None)) else None
    scoped_document_ids = [scoped_document.id] if scoped_document else None
    citations = repositories.search_chunks(session, request.question, limit=max(request.limit, 15), document_ids=scoped_document_ids)

    if not citations:
        scope_label = scoped_document.title if scoped_document else "目前知識庫"
        return {
            "question": request.question,
            "scope": scope_label,
            "answer": "目前在指定範圍內找不到足夠證據回答此問題。",
            "insufficient_evidence": [f"{scope_label} 內未檢索到與問題直接相關的文件片段。"],
            "prompt_version": prompt["version"],
            "citations": [],
            "source_document_ids": scoped_document_ids or [],
            "tool_outputs_used": ["document_search"],
            "needs_human_review": True,
        }

    fallback_lines = []
    for item in citations[:3]:
        fallback_lines.append(f"- {item['title']}: {item['content'][:120]}")
    answer = "根據目前檢索到的文件片段，整理如下：\n" + "\n".join(fallback_lines)

    llm_answer = adapters.call_llm(
        system_prompt=prompt["system_prompt"],
        policy_prompt=prompt["policy_prompt"],
        user_prompt=(
            prompt["user_prompt_template"]
            + "\n\nQuestion:\n"
            + request.question
            + "\n\nRetrieved context:\n"
            + json.dumps(
                [
                    {
                        "title": item["title"],
                        "source_path": item["source_path"],
                        "section_name": item["section_name"],
                        "page_no": item["page_no"],
                        "content": item["content"],
                    }
                    for item in citations
                ],
                ensure_ascii=False,
                indent=2,
            )
        ),
        task_type="knowledge_qa",
    )
    if llm_answer:
        answer = llm_answer

    return {
        "question": request.question,
        "scope": scoped_document.title if scoped_document else "全部已匯入文件",
        "answer": answer,
        "insufficient_evidence": [],
        "prompt_version": prompt["version"],
        "citations": [
            {
                "document_id": item["document_id"],
                "title": item["title"],
                "source_path": item["source_path"],
                "section_name": item["section_name"],
                "page_no": item["page_no"],
                "preview": item["content"][:220],
            }
            for item in citations
        ],
        "source_document_ids": list({item["document_id"] for item in citations}),
        "tool_outputs_used": ["document_search", "knowledge_qa_prompt"],
        "needs_human_review": True,
    }



def answer_with_doc_context(
    session,
    message: str,
    system_prompt: str = "",
    model_override: str | None = None,
    chunk_limit: int = 15,
) -> dict:
    """RAG-enhanced chat: search docs first, then ask LLM with context + analytical role."""
    chunks = repositories.search_chunks(session, message, limit=chunk_limit)

    if chunks:
        context_parts = [
            f"【來源：{c['title']}｜{c['section_name']}】\n{c['content']}"
            for c in chunks[:12]
        ]
        context_block = "\n\n---\n\n".join(context_parts)
        rag_system = (
            (system_prompt + "\n\n" if system_prompt else "")
            + "你是潔沛企業的 ISO 9001:2015 品質管理顧問。"
            "請先以公司文件中的事實為依據，再結合 ISO 9001:2015 最佳實務，"
            "提供具體、可操作的分析與改善建議。"
            "若問題超出文件範圍，仍可引用 ISO 標準給出顧問意見，並清楚標示「顧問建議」與「文件規定」的差異。"
            "回答使用繁體中文，條列式呈現，結尾提供可執行的改善行動項目。"
        )
        rag_user = (
            "以下是從公司文件庫中檢索到的相關段落：\n\n"
            + context_block
            + "\n\n---\n\n請根據上方文件內容及 ISO 9001:2015 專業知識，回答以下問題：\n\n"
            + message
        )
    else:
        rag_system = (
            (system_prompt + "\n\n" if system_prompt else "")
            + "你是潔沛企業的 ISO 9001:2015 品質管理顧問。"
            "公司文件庫中未找到與此問題直接相關的文件，請根據 ISO 9001:2015 最佳實務提供通用顧問建議，"
            "並在回答中說明建議來自 ISO 標準而非公司內部文件。"
            "回答使用繁體中文，條列式呈現。"
        )
        rag_user = message

    result = adapters.call_llm(
        system_prompt=rag_system,
        policy_prompt="",
        user_prompt=rag_user,
        task_type="rag_chat",
        model_override=model_override,
    )

    return {
        "reply": result,
        "doc_chunks_used": len(chunks),
        "citations": [
            {
                "title": c["title"],
                "section": c["section_name"],
                "page_no": c["page_no"],
            }
            for c in chunks[:6]
        ],
    }


def compare_documents(session, request) -> dict:
    left_req = type("LeftReq", (), {"document_id": request.left_document_id, "path": request.left_path})()
    right_req = type("RightReq", (), {"document_id": request.right_document_id, "path": request.right_path})()
    left_doc = _load_or_ingest_single_document(session, left_req)
    right_doc = _load_or_ingest_single_document(session, right_req)

    if left_doc is None or right_doc is None:
        raise ValueError("Both left and right documents must exist. Provide document_id or path for each side.")

    prompt = resolve_prompt(session, "doc_compare")
    cache_payload = {
        "left_document_id": left_doc.id,
        "right_document_id": right_doc.id,
        "left_updated_at": left_doc.updated_at.isoformat() if getattr(left_doc, "updated_at", None) else "",
        "right_updated_at": right_doc.updated_at.isoformat() if getattr(right_doc, "updated_at", None) else "",
        "use_llm": bool(getattr(request, "use_llm", False)),
        "prompt_version": prompt["version"],
    }
    cache_key = hashlib.sha1(json.dumps(cache_payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    cache_entry = repositories.get_compare_cache_by_key(session, cache_key)
    if cache_entry:
        cached = json.loads(cache_entry.response_json)
        cached["cache_hit"] = True
        return cached

    left_rules = engines.run_document_rules(left_doc.full_text)
    right_rules = engines.run_document_rules(right_doc.full_text)

    left_issue_codes = {item["code"]: item for item in left_rules["issues"]}
    right_issue_codes = {item["code"]: item for item in right_rules["issues"]}
    left_only_issues = [left_issue_codes[key] for key in sorted(left_issue_codes.keys() - right_issue_codes.keys())]
    right_only_issues = [right_issue_codes[key] for key in sorted(right_issue_codes.keys() - left_issue_codes.keys())]

    left_lines = [line.strip() for line in left_doc.full_text.splitlines() if line.strip()]
    right_lines = [line.strip() for line in right_doc.full_text.splitlines() if line.strip()]
    diff_lines = list(difflib.unified_diff(left_lines, right_lines, lineterm=""))
    added_lines = [line[1:] for line in diff_lines if line.startswith("+") and not line.startswith("+++")]
    removed_lines = [line[1:] for line in diff_lines if line.startswith("-") and not line.startswith("---")]
    similarity = round(difflib.SequenceMatcher(None, left_doc.full_text, right_doc.full_text).ratio(), 4)
    version_info = _build_version_change_conclusion(
        left_doc,
        right_doc,
        similarity,
        len(added_lines),
        len(removed_lines),
        len(left_only_issues),
        len(right_only_issues),
    )

    if not added_lines and not removed_lines and not left_only_issues and not right_only_issues:
        summary = f"文件 {left_doc.title} 與 {right_doc.title} 在目前文字抽取結果下未偵測到明顯差異。"
    else:
        summary = (
            f"比對 {left_doc.title} 與 {right_doc.title}，文字相似度約 {similarity}。"
            f" 新增重點 {min(len(added_lines), 8)} 項，移除重點 {min(len(removed_lines), 8)} 項，"
            f" 規則缺口左側獨有 {len(left_only_issues)} 項、右側獨有 {len(right_only_issues)} 項。"
        )

    tool_outputs_used = ["document_rule_engine", "text_diff"]
    llm_summary = None
    if getattr(request, "use_llm", False):
        llm_summary = adapters.call_llm(
            system_prompt=prompt["system_prompt"],
            policy_prompt=prompt["policy_prompt"],
            user_prompt=(
                prompt["user_prompt_template"]
                + "\n\nComparison payload:\n"
                + json.dumps(
                    {
                        "left_title": left_doc.title,
                        "right_title": right_doc.title,
                        "similarity": similarity,
                        "left_only_issues": left_only_issues,
                        "right_only_issues": right_only_issues,
                        "added_lines": added_lines[:12],
                        "removed_lines": removed_lines[:12],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            ),
            task_type="doc_compare",
        )
        if llm_summary:
            summary = llm_summary
            tool_outputs_used.append("compare_llm_summary")

    response_data = {
        "left_document": {
            "document_id": left_doc.id,
            "title": left_doc.title,
            "source_path": left_doc.source_path,
            "version": left_doc.version,
        },
        "right_document": {
            "document_id": right_doc.id,
            "title": right_doc.title,
            "source_path": right_doc.source_path,
            "version": right_doc.version,
        },
        "summary": summary,
        "similarity": similarity,
        **version_info,
        "left_only_issues": left_only_issues,
        "right_only_issues": right_only_issues,
        "added_lines": added_lines[:12],
        "removed_lines": removed_lines[:12],
        "prompt_version": prompt["version"],
        "citations": [
            {
                "document_id": left_doc.id,
                "title": left_doc.title,
                "source_path": left_doc.source_path,
                "preview": "\n".join(left_lines[:8])[:220],
            },
            {
                "document_id": right_doc.id,
                "title": right_doc.title,
                "source_path": right_doc.source_path,
                "preview": "\n".join(right_lines[:8])[:220],
            },
        ],
        "source_document_ids": [left_doc.id, right_doc.id],
        "tool_outputs_used": tool_outputs_used,
        "needs_human_review": True,
        "cache_hit": False,
    }
    repositories.upsert_compare_cache(
        session,
        cache_key=cache_key,
        left_document_id=left_doc.id,
        right_document_id=right_doc.id,
        use_llm=bool(getattr(request, "use_llm", False)),
        response_data=response_data,
    )
    repositories.save_compare_result(
        session,
        left_document_id=left_doc.id,
        right_document_id=right_doc.id,
        left_title=left_doc.title,
        right_title=right_doc.title,
        similarity=similarity,
        added_count=len(added_lines),
        removed_count=len(removed_lines),
        conclusion_json=json.dumps(version_info, ensure_ascii=False),
    )
    return response_data


def list_compare_history(session, *, limit: int = 20, offset: int = 0) -> list[dict]:
    rows = repositories.list_compare_results(session, limit=limit, offset=offset)
    return [
        {
            "id": row.id,
            "left_document_id": row.left_document_id,
            "right_document_id": row.right_document_id,
            "left_title": row.left_title,
            "right_title": row.right_title,
            "similarity": row.similarity,
            "added_count": row.added_count,
            "removed_count": row.removed_count,
            "conclusion": json.loads(row.conclusion_json) if row.conclusion_json else {},
            "created_at": row.created_at.isoformat(),
            "created_by": row.created_by,
        }
        for row in rows
    ]
