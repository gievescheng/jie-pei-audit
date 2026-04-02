"""
wafer_spc/spc_engine.py
=======================
玻璃晶圓清洗製程 SPC 計算核心

涵蓋三種管制圖：
  1. Laney u' chart     — Particle 計數（Overdispersion 修正）
  2. I-MR chart         — Thickness 連續量測值
  3. I-MR chart         — TTV 連續量測值

以及製程能力指數：
  Cp / Cpu / Cpl / Cpk / Cpm（含 95% 信賴區間）

Nelson Rules 失控訊號偵測（Rule 1–6）

設計原則：
  - 純 Python + numpy，無外部 SPC 套件相依
  - 所有公開函式回傳 dict，可直接序列化為 JSON 存入 ERPNext DocType
  - 計算邏輯與 Frappe/ERPNext 框架完全解耦，便於單元測試

使用方式（Frappe after_submit hook 中）：
  from wafer_spc.spc_engine import run_imr, run_laney_u, calc_capability
  result = run_imr(thickness_values, usl=705.0, lsl=695.0)

作者：Gieves 品保工程 SPC 系統
版本：1.0
"""

from __future__ import annotations
import numpy as np
from typing import Optional


# ─────────────────────────────────────────────────────────────
#  管制係數常數表（ASTM / Montgomery 標準值）
# ─────────────────────────────────────────────────────────────

# 用於 I-MR chart（子群大小 n=2，即連續兩點的移動極差）
D2 = 1.128   # MR 估計 sigma 的無偏係數
D3 = 0.0     # MR chart LCL 係數
D4 = 3.267   # MR chart UCL 係數

# 滿足 SPC 計算的最小樣本數（少於此值警告但仍計算）
MIN_SAMPLE_WARNING = 25
MIN_SAMPLE_HARD    = 5   # 少於此值直接拒絕計算


# ─────────────────────────────────────────────────────────────
#  1. I-MR 管制圖（Individual & Moving Range）
#     適用：Thickness、TTV 等連續量測值
# ─────────────────────────────────────────────────────────────

def run_imr(
    values: list[float],
    usl: Optional[float] = None,
    lsl: Optional[float] = None,
    target: Optional[float] = None,
    chart_id: str = "",
) -> dict:
    """
    計算 I-MR 管制圖的所有參數。

    Parameters
    ----------
    values  : 按時間順序排列的量測值列表（每批一個值，或每個 Wafer 一個值）
    usl     : 規格上限（用於 Cpk）
    lsl     : 規格下限（用於 Cpk）
    target  : 製程目標值（用於 Cpm，預設為 (USL+LSL)/2）
    chart_id: 管制圖識別碼（存入結果，方便 ERPNext 對應）

    Returns
    -------
    dict 包含：
      x_bar, mr_bar, sigma_mr            — 中心線與估計標準差
      x_ucl, x_lcl                       — X chart 管制界限
      mr_ucl, mr_lcl                     — MR chart 管制界限
      x_values, mr_values                — 原始數據（含移動極差）
      ooc_x, ooc_mr                      — 失控點索引（Rule 1）
      nelson_signals                     — Nelson Rules 1–6 的所有訊號
      capability                         — 製程能力指數（若有規格）
      warnings                           — 資料品質警告列表
      meta                               — 計算摘要資訊
    """
    x = np.asarray(values, dtype=float)
    n = len(x)
    warnings = _check_sample_size(n, "I-MR")

    # 移動極差（n=2）
    mr = np.abs(np.diff(x))

    # 中心線
    x_bar  = float(x.mean())
    mr_bar = float(mr.mean())

    # sigma 估計（以 MR 法，抵抗突發性偏移）
    sigma_mr = mr_bar / D2

    # X chart 管制界限
    x_ucl = x_bar + 3.0 * sigma_mr
    x_lcl = x_bar - 3.0 * sigma_mr

    # MR chart 管制界限
    mr_ucl = D4 * mr_bar
    mr_lcl = D3 * mr_bar   # 永遠為 0

    # Rule 1 失控點（用於基礎紅點標示）
    ooc_x  = [int(i) for i, v in enumerate(x)  if v > x_ucl or v < x_lcl]
    ooc_mr = [int(i) for i, v in enumerate(mr) if v > mr_ucl]

    # Nelson Rules（6 條）
    nelson = _nelson_rules(x, x_bar, sigma_mr)

    # 製程能力
    capability = {}
    if usl is not None or lsl is not None:
        capability = calc_capability(
            values=values,
            usl=usl, lsl=lsl, target=target,
            sigma_override=sigma_mr
        )

    return {
        "chart_id":   chart_id,
        "chart_type": "I-MR",
        "n":          n,
        "x_bar":      round(x_bar, 6),
        "mr_bar":     round(mr_bar, 6),
        "sigma_mr":   round(sigma_mr, 6),
        "x_ucl":      round(x_ucl, 6),
        "x_lcl":      round(x_lcl, 6),
        "mr_ucl":     round(mr_ucl, 6),
        "mr_lcl":     round(mr_lcl, 6),
        "x_values":   [round(float(v), 4) for v in x],
        "mr_values":  [round(float(v), 4) for v in mr],
        "ooc_x":      ooc_x,
        "ooc_mr":     ooc_mr,
        "nelson_signals": nelson,
        "capability": capability,
        "warnings":   warnings,
        "meta": {
            "has_ooc":       len(ooc_x) > 0 or len(ooc_mr) > 0,
            "has_nelson":    bool(nelson),
            "ooc_count_x":  len(ooc_x),
            "ooc_count_mr": len(ooc_mr),
        },
    }


# ─────────────────────────────────────────────────────────────
#  2. Laney u' 管制圖
#     適用：Particle 計數（批次 Wafer 數量不等且可能 Overdispersion）
# ─────────────────────────────────────────────────────────────

def run_laney_u(
    lot_counts: list[dict],
    chart_id: str = "",
) -> dict:
    """
    計算 Laney u' 管制圖。

    Laney u' 的關鍵修正：在標準 u-chart 的 sigma 基礎上，
    乘上由 z_i 標準差估計的 sigma_z，修正 Overdispersion（過度離散）
    或 Underdispersion。sigma_z > 1 表示過度離散，
    此時標準 u chart 的管制界限過窄，會產生大量假警報。

    Parameters
    ----------
    lot_counts : list of dict，每個元素格式：
        {
          "lot_id":  "L001",    # 批號
          "n":       600,       # 本批 Wafer 數（子群大小）
          "defects": 3          # 本批 Particle 計數（整批不合格點總數）
        }

    Returns
    -------
    dict 包含：
      u_bar, sigma_z         — 整體不合格率與離散修正係數
      ucl, lcl               — 各批的動態管制界限（list，長度 = 批數）
      u_i                    — 各批不合格率
      ooc                    — 超出管制界限的批次索引
      nelson_signals         — 僅適用於屬性管制圖的 Rule 1/2/3
      warnings
      meta
    """
    if not lot_counts:
        return {"error": "lot_counts 為空"}

    lot_ids = [d.get("lot_id", str(i)) for i, d in enumerate(lot_counts)]
    n_i     = np.array([d["n"]       for d in lot_counts], dtype=float)
    c_i     = np.array([d["defects"] for d in lot_counts], dtype=float)

    warnings = _check_sample_size(len(lot_counts), "Laney u'")
    if np.any(n_i <= 0):
        warnings.append("部分批次 n ≤ 0，已略過")
        mask = n_i > 0
        n_i, c_i, lot_ids = n_i[mask], c_i[mask], [lot_ids[i] for i in np.where(mask)[0]]

    # 各批不合格率
    u_i   = c_i / n_i
    u_bar = float(c_i.sum() / n_i.sum())

    # 標準化殘差（相對於標準 u chart 期望值）
    se_i  = np.sqrt(u_bar / n_i)          # 標準誤
    z_i   = (u_i - u_bar) / se_i          # 標準化 z 值

    # Laney sigma_z：z_i 的樣本標準差（phi 修正）
    sigma_z = float(z_i.std(ddof=1))

    # 修正後的動態管制界限
    ucl = u_bar + 3.0 * sigma_z * se_i
    lcl = np.maximum(0.0, u_bar - 3.0 * sigma_z * se_i)

    # 失控點
    ooc = [int(i) for i, (u, h, l) in enumerate(zip(u_i, ucl, lcl))
           if u > h or u < l]

    # Nelson Rules（屬性管制圖只用 Rule 1/2/3）
    nelson = _nelson_rules_attribute(u_i, u_bar, sigma_z * se_i)

    return {
        "chart_id":    chart_id,
        "chart_type":  "Laney u'",
        "n_lots":      len(lot_counts),
        "lot_ids":     lot_ids,
        "u_bar":       round(u_bar, 8),
        "sigma_z":     round(sigma_z, 6),
        "overdispersion": sigma_z > 1.0,
        "u_i":         [round(float(v), 8) for v in u_i],
        "ucl":         [round(float(v), 8) for v in ucl],
        "lcl":         [round(float(v), 8) for v in lcl],
        "n_i":         [int(v) for v in n_i],
        "ooc":         ooc,
        "nelson_signals": nelson,
        "warnings":    warnings,
        "meta": {
            "has_ooc":    len(ooc) > 0,
            "has_nelson": bool(nelson),
            "ooc_count":  len(ooc),
            "sigma_z_interpretation": (
                "正常（接近標準 u chart）" if 0.9 <= sigma_z <= 1.1
                else "過度離散（Overdispersion）" if sigma_z > 1.1
                else "低度離散（Underdispersion）"
            ),
        },
    }


# ─────────────────────────────────────────────────────────────
#  3. 製程能力指數
#     Cp / Cpu / Cpl / Cpk / Cpm  + 95% 信賴區間
# ─────────────────────────────────────────────────────────────

def calc_capability(
    values: list[float],
    usl: Optional[float] = None,
    lsl: Optional[float] = None,
    target: Optional[float] = None,
    sigma_override: Optional[float] = None,
    confidence: float = 0.95,
) -> dict:
    """
    計算製程能力指數。

    sigma 估計優先順序：
      1. sigma_override（由呼叫端傳入，通常是 I-MR 計算出的 sigma_mr）
      2. 以移動極差自行估計（MR 法）
      3. 樣本標準差（s 法，僅在 MR 計算失敗時回退）

    Parameters
    ----------
    values          : 量測值列表
    usl, lsl        : 規格上下限（至少一個）
    target          : 目標值（Cpm 使用），預設為 (USL+LSL)/2
    sigma_override  : 直接指定 sigma（通常由 run_imr 傳入 sigma_mr）
    confidence      : 信賴水準（預設 0.95）

    Returns
    -------
    dict 包含 Cp, Cpu, Cpl, Cpk, Cpm 及各自的信賴區間
    """
    x = np.asarray(values, dtype=float)
    n = len(x)
    x_bar = float(x.mean())

    # sigma 估計
    if sigma_override is not None:
        sigma = float(sigma_override)
        sigma_method = "MR（外部傳入）"
    elif n >= 2:
        mr = np.abs(np.diff(x))
        sigma = float(mr.mean()) / D2
        sigma_method = "MR（內部計算）"
    else:
        sigma = float(x.std(ddof=1))
        sigma_method = "s（樣本標準差）"

    if sigma <= 0:
        return {"error": "sigma ≤ 0，無法計算製程能力"}

    result: dict = {
        "n": n,
        "mean": round(x_bar, 6),
        "sigma": round(sigma, 6),
        "sigma_method": sigma_method,
        "usl": usl,
        "lsl": lsl,
    }

    # Cp（雙邊）
    if usl is not None and lsl is not None:
        cp  = (usl - lsl) / (6.0 * sigma)
        cpu = (usl - x_bar) / (3.0 * sigma)
        cpl = (x_bar - lsl) / (3.0 * sigma)
        cpk = min(cpu, cpl)

        # Cpm（考慮偏移）
        t = target if target is not None else (usl + lsl) / 2.0
        sigma_pm = np.sqrt(sigma**2 + (x_bar - t)**2)
        cpm = (usl - lsl) / (6.0 * float(sigma_pm))

        # Cpk 信賴區間（Bissell 近似法）
        z = _z_score(confidence)
        cpk_margin = z * np.sqrt(1.0 / (9.0 * n * cpk**2) + 1.0 / (2.0 * (n - 1)))
        cpk_ci = (
            round(float(cpk * (1.0 - cpk_margin)), 4),
            round(float(cpk * (1.0 + cpk_margin)), 4),
        )

        result.update({
            "cp":    round(float(cp),  4),
            "cpu":   round(float(cpu), 4),
            "cpl":   round(float(cpl), 4),
            "cpk":   round(float(cpk), 4),
            "cpm":   round(float(cpm), 4),
            "cpk_ci":          cpk_ci,
            "cpk_ci_level":    confidence,
            "target":          round(float(t), 4),
            "mean_shift_sigma": round(abs(x_bar - t) / sigma, 4),
            "grade": _capability_grade(cpk),
        })

    # 單邊能力（只有 USL 或只有 LSL）
    elif usl is not None:
        cpu = (usl - x_bar) / (3.0 * sigma)
        result.update({"cpu": round(float(cpu), 4), "grade": _capability_grade(cpu)})
    elif lsl is not None:
        cpl = (x_bar - lsl) / (3.0 * sigma)
        result.update({"cpl": round(float(cpl), 4), "grade": _capability_grade(cpl)})

    return result


# ─────────────────────────────────────────────────────────────
#  4. Nelson / Western Electric 失控訊號偵測
# ─────────────────────────────────────────────────────────────

def _nelson_rules(
    x: np.ndarray,
    x_bar: float,
    sigma: float,
) -> dict[str, list[int]]:
    """
    偵測 Nelson Rules 1–6（計量管制圖適用）。
    回傳 {rule_id: [觸發的點索引列表]}，未觸發的 rule 不出現在 dict 中。

    Rules 定義：
      1. 任一點超出 ±3σ
      2. 連續 9 點落在中心線同側
      3. 連續 6 點單調遞增或遞減
      4. 連續 14 點交替上下
      5. 連續 3 點中有 2 點超出 ±2σ 同側
      6. 連續 5 點中有 4 點超出 ±1σ 同側
    """
    n = len(x)
    signals: dict[str, list[int]] = {}

    # Rule 1：任一點超出 ±3σ
    r1 = [i for i, v in enumerate(x) if abs(v - x_bar) > 3.0 * sigma]
    if r1:
        signals["rule_1_beyond_3sigma"] = r1

    # Rule 2：連續 9 點同側（≥ 9 個才能觸發）
    if n >= 9:
        r2 = []
        for i in range(8, n):
            window = x[i - 8: i + 1]
            if all(v > x_bar for v in window) or all(v < x_bar for v in window):
                r2.append(i)
        if r2:
            signals["rule_2_nine_same_side"] = r2

    # Rule 3：連續 6 點單調（≥ 6 個才能觸發）
    if n >= 6:
        r3 = []
        for i in range(5, n):
            window = x[i - 5: i + 1]
            diffs = np.diff(window)
            if all(d > 0 for d in diffs) or all(d < 0 for d in diffs):
                r3.append(i)
        if r3:
            signals["rule_3_six_monotone"] = r3

    # Rule 4：連續 14 點交替上下
    if n >= 14:
        r4 = []
        for i in range(13, n):
            window = x[i - 13: i + 1]
            diffs = np.diff(window)
            if all(diffs[j] * diffs[j + 1] < 0 for j in range(len(diffs) - 1)):
                r4.append(i)
        if r4:
            signals["rule_4_fourteen_alternating"] = r4

    # Rule 5：連續 3 點中 2 點超出 ±2σ 同側
    if n >= 3:
        r5 = []
        for i in range(2, n):
            window = x[i - 2: i + 1]
            above = sum(1 for v in window if v > x_bar + 2.0 * sigma)
            below = sum(1 for v in window if v < x_bar - 2.0 * sigma)
            if above >= 2 or below >= 2:
                r5.append(i)
        if r5:
            signals["rule_5_two_of_three_2sigma"] = r5

    # Rule 6：連續 5 點中 4 點超出 ±1σ 同側
    if n >= 5:
        r6 = []
        for i in range(4, n):
            window = x[i - 4: i + 1]
            above = sum(1 for v in window if v > x_bar + sigma)
            below = sum(1 for v in window if v < x_bar - sigma)
            if above >= 4 or below >= 4:
                r6.append(i)
        if r6:
            signals["rule_6_four_of_five_1sigma"] = r6

    return signals


def _nelson_rules_attribute(
    u_i: np.ndarray,
    u_bar: float,
    se_i: np.ndarray,
) -> dict[str, list[int]]:
    """
    屬性管制圖（Laney u'）僅套用 Rule 1/2/3，
    且以動態 sigma（se_i）取代固定 sigma。
    """
    n = len(u_i)
    signals: dict[str, list[int]] = {}

    # Rule 1
    r1 = [i for i, (u, s) in enumerate(zip(u_i, se_i))
          if abs(u - u_bar) > 3.0 * s]
    if r1:
        signals["rule_1_beyond_3sigma"] = r1

    # Rule 2（連續 9 點同側）
    if n >= 9:
        r2 = []
        for i in range(8, n):
            window = u_i[i - 8: i + 1]
            if all(v > u_bar for v in window) or all(v < u_bar for v in window):
                r2.append(i)
        if r2:
            signals["rule_2_nine_same_side"] = r2

    # Rule 3（連續 6 點單調）
    if n >= 6:
        r3 = []
        for i in range(5, n):
            window = u_i[i - 5: i + 1]
            diffs = np.diff(window)
            if all(d > 0 for d in diffs) or all(d < 0 for d in diffs):
                r3.append(i)
        if r3:
            signals["rule_3_six_monotone"] = r3

    return signals


# ─────────────────────────────────────────────────────────────
#  5. ERPNext 整合進入點（after_submit hook 呼叫）
# ─────────────────────────────────────────────────────────────

def run_all_charts(
    thickness_values: list[float],
    ttv_values: list[float],
    particle_lots: list[dict],
    spec: dict,
) -> dict:
    """
    一次計算三張管制圖並回傳結構化結果。
    供 Frappe after_submit hook 呼叫：

        from wafer_spc.spc_engine import run_all_charts
        result = run_all_charts(
            thickness_values=[702.1, 701.3, ...],
            ttv_values=[0.28, 0.19, ...],
            particle_lots=[{"lot_id":"L001","n":600,"defects":3}, ...],
            spec={
                "thickness_usl": 705.0, "thickness_lsl": 695.0,
                "ttv_usl": 2.0,         "ttv_lsl": 0.0,
                "particle_target_rate": 0.005,
            }
        )

    Parameters
    ----------
    thickness_values : 按時間排序的 Thickness 量測值
    ttv_values       : 按時間排序的 TTV 量測值
    particle_lots    : Particle 計數批次列表（Laney u' 使用）
    spec             : 規格字典

    Returns
    -------
    {
      "thickness": {...},    # I-MR 結果
      "ttv":       {...},    # I-MR 結果
      "particle":  {...},    # Laney u' 結果
      "summary":   {...},    # 整體狀態摘要
    }
    """
    thickness_result = run_imr(
        values=thickness_values,
        usl=spec.get("thickness_usl"),
        lsl=spec.get("thickness_lsl"),
        chart_id="thickness_imr",
    ) if thickness_values else {}

    ttv_result = run_imr(
        values=ttv_values,
        usl=spec.get("ttv_usl"),
        lsl=spec.get("ttv_lsl"),
        chart_id="ttv_imr",
    ) if ttv_values else {}

    particle_result = run_laney_u(
        lot_counts=particle_lots,
        chart_id="particle_laney_u",
    ) if particle_lots else {}

    any_ooc = (
        thickness_result.get("meta", {}).get("has_ooc", False) or
        ttv_result.get("meta", {}).get("has_ooc", False) or
        particle_result.get("meta", {}).get("has_ooc", False)
    )
    any_nelson = (
        bool(thickness_result.get("nelson_signals")) or
        bool(ttv_result.get("nelson_signals")) or
        bool(particle_result.get("nelson_signals"))
    )

    return {
        "thickness": thickness_result,
        "ttv":       ttv_result,
        "particle":  particle_result,
        "summary": {
            "any_ooc":        any_ooc,
            "any_nelson":     any_nelson,
            "needs_attention": any_ooc or any_nelson,
            "thickness_cpk":  thickness_result.get("capability", {}).get("cpk"),
            "ttv_cpk":        ttv_result.get("capability", {}).get("cpk"),
        },
    }


# ─────────────────────────────────────────────────────────────
#  6. 工具函式
# ─────────────────────────────────────────────────────────────

def _check_sample_size(n: int, chart_name: str) -> list[str]:
    warnings = []
    if n < MIN_SAMPLE_HARD:
        warnings.append(
            f"[{chart_name}] 樣本數 n={n} 過少（最低要求 {MIN_SAMPLE_HARD}），計算結果不可靠"
        )
    elif n < MIN_SAMPLE_WARNING:
        warnings.append(
            f"[{chart_name}] 樣本數 n={n} 偏少，建議至少 {MIN_SAMPLE_WARNING} 筆以上"
        )
    return warnings


def _z_score(confidence: float) -> float:
    """回傳常態分配的雙尾 z 值，例如 0.95 → 1.96"""
    from scipy.stats import norm
    return float(norm.ppf((1.0 + confidence) / 2.0))


def _capability_grade(cpk: float) -> str:
    """依 Cpk 值回傳製程能力等級判定"""
    if cpk >= 1.67:
        return "A+ (≥1.67)：超優"
    elif cpk >= 1.33:
        return "A  (≥1.33)：優良"
    elif cpk >= 1.00:
        return "B  (≥1.00)：尚可，需改善"
    elif cpk >= 0.67:
        return "C  (≥0.67)：不足"
    else:
        return "D  (<0.67)：製程失控"
