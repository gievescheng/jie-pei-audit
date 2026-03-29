from __future__ import annotations

import math
import statistics

REQUIRED_DOCUMENT_RULES = [
    ("purpose", ["目的"], "缺少目的章節"),
    ("scope", ["範圍"], "缺少範圍章節"),
    ("responsibility", ["職責", "權責"], "缺少職責或權責章節"),
    ("process", ["流程", "作業內容", "程序"], "缺少流程或作業內容章節"),
    ("forms", ["表單"], "缺少表單章節"),
    ("records", ["記錄"], "缺少記錄章節"),
    ("version", ["版次", "版本"], "缺少版次或版本資訊"),
    ("approval", ["核准", "審核", "製表"], "缺少核准或審核欄位"),
    ("retention", ["保存", "保存期限"], "缺少保存規則"),
]


def run_document_rules(text: str) -> dict:
    lowered = text.lower()
    issues = []
    insufficient = []
    for code, keywords, title in REQUIRED_DOCUMENT_RULES:
        found = any(keyword.lower() in lowered for keyword in keywords)
        if found:
            continue
        severity = "high" if code in {"version", "approval", "retention"} else "medium"
        issues.append(
            {
                "code": code,
                "title": title,
                "severity": severity,
                "description": f"文件全文中未偵測到關鍵字: {', '.join(keywords)}",
            }
        )
        if code in {"approval", "retention"}:
            insufficient.append(f"未能確認 {title.replace('缺少', '')}，需人工覆核原文件版面。")
    return {"issues": issues, "insufficient_evidence": insufficient}



def parse_numeric_values(values: list[float], csv_text: str) -> list[float]:
    parsed = [float(value) for value in values]
    if csv_text.strip():
        for part in csv_text.replace("\n", ",").split(","):
            cell = part.strip()
            if cell:
                parsed.append(float(cell))
    if len(parsed) < 2:
        raise ValueError("SPC 分析至少需要 2 個數值點。")
    return parsed



def compute_spc_metrics(values: list[float], *, lsl: float | None, usl: float | None, target: float | None) -> tuple[dict, list[dict]]:
    avg = statistics.fmean(values)
    stdev = statistics.stdev(values) if len(values) > 1 else 0.0
    variance = statistics.variance(values) if len(values) > 1 else 0.0
    out_of_spec = []
    for idx, value in enumerate(values, start=1):
        if lsl is not None and value < lsl:
            out_of_spec.append({"index": idx, "value": value, "type": "below_lsl"})
        if usl is not None and value > usl:
            out_of_spec.append({"index": idx, "value": value, "type": "above_usl"})

    cp = cpk = pp = ppk = None
    if stdev > 0 and lsl is not None and usl is not None:
        cp = (usl - lsl) / (6 * stdev)
        cpk = min((usl - avg) / (3 * stdev), (avg - lsl) / (3 * stdev))
        pp = cp
        ppk = cpk

    drift = values[-1] - values[0]
    trend = "up" if drift > 0 else "down" if drift < 0 else "flat"
    sigma_level = None
    if stdev > 0 and target is not None:
        sigma_level = abs(avg - target) / stdev

    metrics = {
        "count": len(values),
        "mean": round(avg, 4),
        "stdev": round(stdev, 4),
        "variance": round(variance, 4),
        "min": round(min(values), 4),
        "max": round(max(values), 4),
        "lsl": lsl,
        "usl": usl,
        "target": target,
        "cp": round(cp, 4) if cp is not None else None,
        "cpk": round(cpk, 4) if cpk is not None else None,
        "pp": round(pp, 4) if pp is not None else None,
        "ppk": round(ppk, 4) if ppk is not None else None,
        "sigma_level": round(sigma_level, 4) if sigma_level is not None and math.isfinite(sigma_level) else None,
        "out_of_spec_count": len(out_of_spec),
        "trend": trend,
        "drift": round(drift, 4),
    }
    return metrics, out_of_spec



def build_spc_summaries(parameter_name: str, metrics: dict, abnormal_items: list[dict]) -> tuple[str, str]:
    engineering = (
        f"{parameter_name} 共分析 {metrics['count']} 筆資料，平均值 {metrics['mean']}，標準差 {metrics['stdev']}。"
    )
    if metrics.get("cpk") is not None:
        engineering += f" Cp={metrics['cp']}，Cpk={metrics['cpk']}。"
    engineering += f" 趨勢為 {metrics['trend']}，超規筆數 {metrics['out_of_spec_count']}。"

    if abnormal_items:
        management = (
            f"{parameter_name} 偵測到 {len(abnormal_items)} 筆超規資料，建議優先確認製程條件與量測系統，並安排人工覆核。"
        )
    elif metrics.get("cpk") is not None and metrics["cpk"] < 1.33:
        management = (
            f"{parameter_name} 雖未出現超規，但製程能力不足，Cpk 低於 1.33，建議檢討中心化與變異控制。"
        )
    else:
        management = f"{parameter_name} 目前未見明顯風險，可持續依既有頻率監控。"
    return engineering, management



def build_deviation_draft(issue_description: str, process_step: str, lot_no: str, severity: str) -> dict:
    causes = []
    if any(keyword in issue_description for keyword in ["破", "裂", "碎"]):
        causes.extend([
            "搬運或取放過程缺少防護，造成材料受力破損。",
            "治具或載具狀態異常，導致接觸點集中受力。",
            "作業動線與暫存區配置不佳，增加碰撞風險。",
        ])
    if any(keyword in issue_description for keyword in ["污染", "異物", "AOI"]):
        causes.extend([
            "清潔或過濾條件不足，造成異物殘留。",
            "AOI 判定條件與實際缺陷型態未完全對齊。",
        ])
    if not causes:
        causes.extend([
            "作業條件控制不足。",
            "設備或量測系統狀態需進一步確認。",
            "文件化作業要求與現場執行存在落差。",
        ])

    known_facts = [f"問題描述: {issue_description}", f"嚴重度: {severity}"]
    if process_step:
        known_facts.append(f"製程步驟: {process_step}")
    if lot_no:
        known_facts.append(f"批號: {lot_no}")

    return {
        "known_facts": known_facts,
        "possible_causes": causes,
        "containment_actions": [
            "先隔離相關批次、在製品與可疑物料，避免持續流出。",
            "立即確認現場是否仍存在相同異常條件，必要時暫停該工序。",
        ],
        "permanent_actions": [
            "修訂作業標準與檢查點，補強防呆與覆核機制。",
            "針對人員、設備、方法與材料分別追查，建立 CAPA 責任與期限。",
        ],
        "verification_plan": [
            "連續追蹤至少 3 批或 1 週的同製程資料，確認異常未再發。",
            "以複驗結果與稽核證據確認矯正措施有效，再評估結案。",
        ],
    }
