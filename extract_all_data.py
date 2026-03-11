"""
extract_all_data.py
讀取各模組 DOCX 記錄文件，輸出 JS 陣列供貼入 audit-dashboard.jsx
"""
import zipfile, xml.etree.ElementTree as ET, re, os, sys
from pathlib import Path

BASE = Path(r"C:\Users\USER\Desktop\自動稽核程式")
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

# ── 基礎工具 ──────────────────────────────────────────────────────────────────

def cell_text(tc):
    return re.sub(r"\s+", " ",
        "".join(t.text or "" for t in tc.iter(f"{{{W}}}t"))).strip()

def read_tables(path, max_rows=60):
    """回傳 list[list[list[str]]] : tables → rows → cells"""
    try:
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml")
        root = ET.fromstring(xml)
        out = []
        for tbl in root.iter(f"{{{W}}}tbl"):
            rows = []
            for tr in tbl.iter(f"{{{W}}}tr"):
                cells = [cell_text(tc) for tc in tr.iter(f"{{{W}}}tc")]
                if any(cells):
                    rows.append(cells)
                if len(rows) >= max_rows:
                    break
            if rows:
                out.append(rows)
        return out
    except Exception as e:
        print(f"  !! read_tables ERROR {path}: {e}", file=sys.stderr)
        return []

def read_paragraphs(path):
    try:
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml")
        root = ET.fromstring(xml)
        return [re.sub(r"\s+", " ",
                "".join(t.text or "" for t in p.iter(f"{{{W}}}t"))).strip()
                for p in root.iter(f"{{{W}}}p") if "".join(
                    t.text or "" for t in p.iter(f"{{{W}}}t")).strip()]
    except:
        return []

def tw_date(s):
    """'114/09/04' → '2025-09-04'; '2025/11/12' → '2025-11-12'"""
    s = s.strip().replace(".", "/")
    m = re.match(r"(\d{2,4})[/年](\d{1,2})[/月](\d{1,2})", s)
    if not m:
        return ""
    y, mo, d = m.groups()
    if len(y) <= 3:          # 民國
        y = str(int(y) + 1911)
    return f"{y}-{int(mo):02d}-{int(d):02d}"

def js_str(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')

def find(path_rel):
    p = BASE / path_rel
    return p if p.exists() else None

# ── 1. 訓練管理 initialTraining ───────────────────────────────────────────────

# 員工基本資料：從 9.2 合格稽核員名冊 + 訓練紀錄檔案名稱補足
EMPLOYEE_INFO = {
    "劉哲驊": {"dept": "管理部", "role": "協理",   "hireDate": "2021-07-01"},
    "蔡有為": {"dept": "管理部", "role": "部長",   "hireDate": "2021-07-01"},
    "林佑翰": {"dept": "業務部", "role": "組長",   "hireDate": "2022-09-01"},
    "詹博智": {"dept": "生產課", "role": "組長",   "hireDate": "2024-03-01"},
    "程鼎智": {"dept": "品管課", "role": "課長",   "hireDate": "2021-07-01"},
    "吳澤仁": {"dept": "業務部", "role": "部長",   "hireDate": "2021-07-01"},
    "林育陞": {"dept": "",      "role": "",       "hireDate": ""},
    "楊麗璇": {"dept": "",      "role": "",       "hireDate": ""},
    "朱姿霖": {"dept": "",      "role": "",       "hireDate": ""},
    "陳宥穎": {"dept": "",      "role": "",       "hireDate": ""},
}

def parse_training_file(path):
    """解析個人訓練紀錄表，回傳訓練紀錄 list"""
    tables = read_tables(path)
    records = []
    if not tables:
        return records
    # 通常第一張（或唯一張）表是訓練紀錄
    for tbl in tables:
        for row in tbl:
            # 跳過 header 行（含 '課程' '訓練' '日期' 等關鍵字）
            joined = "".join(row)
            if any(k in joined for k in ["課程名稱", "訓練課程", "訓練日期", "序號", "編號", "培訓"]):
                continue
            # 跳過全空
            if not joined.strip():
                continue
            # 嘗試取得日期（yyyymmdd 或 民國年）
            date_str = ""
            course_str = ""
            type_str = ""
            result_str = "合格"
            cert_str = ""
            for cell in row:
                # 日期格式偵測
                if re.search(r"\d{3,4}[./年]\d{1,2}[./月]\d{1,2}", cell) and not date_str:
                    date_str = tw_date(re.search(
                        r"\d{3,4}[./年]\d{1,2}[./月]\d{1,2}", cell).group())
                elif re.search(r"\d{4}[-/]\d{2}[-/]\d{2}", cell) and not date_str:
                    date_str = cell.strip()[:10].replace("/", "-")
                # 訓練類別
                if "外訓" in cell:
                    type_str = "外訓"
                elif "內訓" in cell:
                    type_str = "內訓"
                # 合格/通過
                if any(k in cell for k in ["合格", "通過", "Pass"]):
                    result_str = "合格"
                # 有無證書
                if "有" == cell.strip():
                    cert_str = "有"
                elif "無" == cell.strip():
                    cert_str = "無"
            # 課程名稱：取最長的、非數字單格
            candidates = [c for c in row if len(c) > 4 and not re.match(r"^\d+$", c)
                          and not re.search(r"\d{3,4}[./年]", c)]
            if candidates:
                course_str = max(candidates, key=len)
            # 過濾：沒有課程名稱或日期視為無效
            if not course_str and not date_str:
                continue
            records.append({
                "course": course_str,
                "date": date_str,
                "type": type_str or "內訓",
                "result": result_str,
                "cert": cert_str or "無",
            })
    return records

def extract_training():
    rec_dir = BASE / "3 人力資源及訓練管理程序" / "記錄"
    entries = []
    emp_id = 1
    for fname in sorted(rec_dir.glob("3.4.*.docx")):
        # 從檔名取員工姓名：3.4.2 教育訓練紀錄表(蔡有為).docx
        m = re.search(r"[（(]([^）)]+)[）)]", fname.name)
        if not m:
            continue
        name = m.group(1)
        info = EMPLOYEE_INFO.get(name, {"dept": "", "role": "", "hireDate": ""})
        trainings = parse_training_file(fname)
        entries.append({
            "id": f"EMP-{emp_id:03d}",
            "name": name,
            "dept": info["dept"],
            "role": info["role"],
            "hireDate": info["hireDate"],
            "trainings": trainings,
        })
        emp_id += 1
        print(f"  訓練 {name}: {len(trainings)} 筆", file=sys.stderr)
    return entries

# ── 2. 設備保養 initialEquipment ──────────────────────────────────────────────

# 設備基本對照（從 4.5.1 年度計劃表已確認）
EQUIPMENT_BASE = [
    {"id": "JE-001", "name": "超音波清洗機",  "location": "生產課", "intervalDays": 30},
    {"id": "JE-002", "name": "終端清洗機",    "location": "生產課", "intervalDays": 90},
    {"id": "JE-003", "name": "OCR 篩選機",   "location": "生產課", "intervalDays": 90},
    {"id": "JE-004", "name": "AOI 自動光學檢測儀", "location": "品管課", "intervalDays": 90},
    {"id": "JE-005", "name": "WAFER 厚度量測系統", "location": "品管課", "intervalDays": 180},
    {"id": "JE-006", "name": "NAS 網路儲存系統",  "location": "管理部", "intervalDays": 365},
]

# 對應 4.4.X 檔名關鍵字
EQUIP_FILE_MAP = {
    "超音波清洗機": "4.4.1",
    "終端清洗機":   "4.4.2",
    "OCR":         "4.4.3",
    "AOI":         "4.4.4",
    "TTV":         "4.4.5",
    "NAS":         "4.4.6",
}

NEXT_ITEMS_MAP = {
    "JE-001": ["清洗槽清潔", "超音波強度確認", "加熱溫度校驗", "排水管路檢查"],
    "JE-002": ["清洗槽清潔", "藥液濃度確認", "噴嘴清潔", "馬達運轉確認"],
    "JE-003": ["光學鏡頭清潔", "排序正確性確認", "定位精度確認", "傳送帶清潔"],
    "JE-004": ["光源強度校驗", "鏡頭清潔", "定位精度確認", "軟體更新確認"],
    "JE-005": ["量測精度確認", "探針清潔", "真空系統確認", "定位校驗"],
    "JE-006": ["硬碟健康狀態確認", "備份完整性確認", "網路連線確認", "UPS 電池確認"],
}

def parse_maintenance_card(path):
    """從設備維護履歷卡取得最後保養日期"""
    tables = read_tables(path)
    last_date = ""
    for tbl in tables:
        for row in tbl:
            joined = "".join(row)
            # 找包含日期的列（保養記錄行）
            m = re.search(r"(\d{2,4})[./年](\d{1,2})[./月](\d{1,2})", joined)
            if m:
                candidate = tw_date(m.group())
                if candidate > last_date:
                    last_date = candidate
    return last_date

def extract_equipment():
    rec_dir = BASE / "4 設施設備管理程序" / "記錄"
    entries = []
    for eq in EQUIPMENT_BASE:
        # 找對應履歷卡
        key = [k for k in EQUIP_FILE_MAP if k in eq["name"] or k in eq["id"]]
        prefix = EQUIP_FILE_MAP.get(key[0], "") if key else ""
        maint_path = None
        if prefix:
            for f in rec_dir.glob(f"{prefix}*.docx"):
                maint_path = f
                break
        last_maint = parse_maintenance_card(maint_path) if maint_path else ""
        entries.append({
            "id": eq["id"],
            "name": eq["name"],
            "location": eq["location"],
            "lastMaintenance": last_maint,
            "intervalDays": eq["intervalDays"],
            "nextItems": NEXT_ITEMS_MAP.get(eq["id"], []),
        })
        print(f"  設備 {eq['id']} {eq['name']}: 最後保養 {last_maint or '無紀錄'}", file=sys.stderr)
    return entries

# ── 3. 供應商管理 initialSuppliers ────────────────────────────────────────────

SUPPLIER_BASE = {
    "楊特":   {"id": "SUP-001", "category": "耗材",   "contact": ""},
    "金華瑋": {"id": "SUP-002", "category": "設備零件", "contact": ""},
    "柏連":   {"id": "SUP-003", "category": "化學品",  "contact": ""},
    "鏵友益": {"id": "SUP-004", "category": "電子零件", "contact": ""},
    "奈米趨勢":{"id": "SUP-005","category": "量測設備", "contact": ""},
    "拓生科技":{"id": "SUP-006","category": "量測設備", "contact": ""},
}

def parse_supplier_eval(path):
    """從供應商定期評鑑表讀取分數、日期、名稱、問題"""
    tables = read_tables(path)
    score = 0
    eval_date = ""
    full_name = ""
    issues = []
    paras = read_paragraphs(path)
    # 從段落找公司名稱
    for p in paras[:10]:
        if any(k in p for k in ["供應商名稱", "廠商名稱", "公司名稱"]):
            m = re.search(r"[：:]\s*(.+)", p)
            if m:
                full_name = m.group(1).strip()
        if any(k in p for k in ["評鑑日期", "評估日期", "填表日期"]):
            m = re.search(r"(\d{2,4})[./年]\d{1,2}[./月]\d{1,2}", p)
            if m:
                eval_date = tw_date(m.group())
    for tbl in tables:
        for row in tbl:
            joined = "".join(row)
            # 找總分行
            if any(k in joined for k in ["總分", "合計", "小計"]) and not score:
                for cell in row:
                    m = re.search(r"(\d{2,3})", cell)
                    if m:
                        v = int(m.group(1))
                        if 40 <= v <= 100:
                            score = v
                            break
            # 找日期
            m_date = re.search(r"(\d{2,4})[./年](\d{1,2})[./月](\d{1,2})", joined)
            if m_date and not eval_date:
                eval_date = tw_date(m_date.group())
            # 找問題（有備註/問題/缺失 欄位非空的行）
            if any(k in joined for k in ["延誤", "不符", "缺失", "問題", "改善"]):
                # 取最後一格非空
                remark = [c for c in row if c and len(c) > 3
                          and not any(k in c for k in ["備註", "意見", "問題"])]
                if remark:
                    issues.append(remark[-1])
    return {"score": score, "evalDate": eval_date, "fullName": full_name, "issues": issues[:3]}

def extract_suppliers():
    rec_dir = BASE / "10 採購及供應商管理程序" / "記錄"
    entries = []
    for fname in sorted(rec_dir.glob("10.3.[1-9]*.docx")):
        # 從檔名取供應商關鍵字
        matched_key = None
        for k in SUPPLIER_BASE:
            if k in fname.name:
                matched_key = k
                break
        if not matched_key:
            continue
        info = SUPPLIER_BASE[matched_key]
        data = parse_supplier_eval(fname)
        score = data["score"] or 0
        result = "優良" if score >= 90 else ("合格" if score >= 75 else "條件合格")
        full_name = data["fullName"] or (matched_key + "企業")
        entries.append({
            "id": info["id"],
            "name": full_name or matched_key,
            "category": info["category"],
            "contact": info["contact"],
            "lastEvalDate": data["evalDate"],
            "evalScore": score,
            "evalResult": result,
            "evalIntervalDays": 365,
            "issues": data["issues"],
        })
        print(f"  供應商 {matched_key}: 分數={score}, 日期={data['evalDate']}", file=sys.stderr)
    return entries

# ── 4. 不符合管理 initialNonConformances ──────────────────────────────────────

def parse_nc_report(path, nc_id):
    """解析不符合及矯正措施報告表"""
    tables = read_tables(path)
    date = dept = type_ = desc = cause = action = resp = due = status = close = ""
    severity = "輕微"
    for tbl in tables:
        for row in tbl:
            joined = "".join(row)
            # 日期
            m = re.search(r"(\d{2,4})[./年](\d{1,2})[./月](\d{1,2})", joined)
            if m and not date:
                date = tw_date(m.group())
            # 部門
            for cell in row:
                if any(k in cell for k in ["品管課", "生產課", "管理部", "業務部", "品檢課", "資材課"]):
                    if not dept:
                        dept = re.search(r"(品管課|生產課|管理部|業務部|品檢課|資材課)", cell).group()
                # 不符合類型
                if any(k in cell for k in ["製程異常", "量測異常", "來料不合格", "文件不符",
                                            "人員作業", "設備異常", "不合格品"]):
                    if not type_:
                        for k in ["製程異常", "量測異常", "來料不合格", "文件不符",
                                  "人員作業", "設備異常", "不合格品"]:
                            if k in cell:
                                type_ = k
                                break
                # 嚴重程度
                if "重大" in cell:
                    severity = "重大"
                # 描述（長文字）
                if len(cell) > 20 and not desc:
                    desc = cell[:100]
                # 原因分析
                if ("原因" in joined or "分析" in joined) and len(cell) > 10 and not cause:
                    cause = cell[:80]
                # 矯正措施
                if ("矯正" in joined or "改善" in joined) and len(cell) > 10 and not action:
                    action = cell[:80]
                # 負責人
                if any(k in cell for k in ["負責", "承辦", "執行人"]):
                    m2 = re.search(r"[：:]\s*(\S+)", cell)
                    if m2 and not resp:
                        resp = m2.group(1)
    # 狀態：從 15.1.1 = 2025, 15.1.2 = 2026
    if "15.1.1" in str(path):
        status = "已關閉"
        close = date
    else:
        status = "處理中"
    if not type_:
        type_ = "文件不符"
    return {
        "id": nc_id,
        "date": date,
        "dept": dept or "品管課",
        "type": type_,
        "description": desc or "詳見不符合及矯正措施報告表",
        "severity": severity,
        "rootCause": cause or "",
        "correctiveAction": action or "",
        "responsible": resp or "",
        "dueDate": "",
        "status": status,
        "closeDate": close if status == "已關閉" else "",
        "effectiveness": "有效" if status == "已關閉" else "",
    }

def extract_nc():
    nc_dir = BASE / "15 不符合及矯正措施管理程序" / "記錄"
    entries = []
    for fname, nc_id in [
        ("15.1.1不符合及矯正措施報告表.docx", "NC-2025-001"),
        ("15.1.2不符合及矯正措施報告表.docx", "NC-2026-001"),
    ]:
        p = nc_dir / fname
        if p.exists():
            rec = parse_nc_report(p, nc_id)
            entries.append(rec)
            print(f"  NC {nc_id}: 日期={rec['date']}, 部門={rec['dept']}", file=sys.stderr)
    return entries

# ── 5. 稽核計畫 initialAuditPlans ─────────────────────────────────────────────

def parse_audit_report(path):
    """解析 9.5 品質稽核報告書，回傳基本欄位"""
    tables = read_tables(path)
    paras = read_paragraphs(path)
    date = scope_dept = auditor = auditee = ""
    ok_count = ng_count = 0
    for tbl in tables:
        for row in tbl:
            joined = "".join(row)
            m = re.search(r"(\d{2,4})[./年](\d{1,2})[./月](\d{1,2})", joined)
            if m and not date:
                date = tw_date(m.group())
            if "OK" in joined or "合格" in joined:
                ok_count += joined.count("OK") + joined.count("○")
            if "NG" in joined or "不合格" in joined:
                ng_count += joined.count("NG") + joined.count("×")
    for p in paras:
        if "稽核員" in p or "稽核人員" in p:
            m = re.search(r"[：:]\s*(\S+)", p)
            if m and not auditor:
                auditor = m.group(1)
        if "受稽核" in p or "稽核部門" in p:
            m = re.search(r"[：:]\s*(\S+)", p)
            if m and not scope_dept:
                scope_dept = m.group(1)
    return {"date": date, "auditor": auditor, "dept": scope_dept,
            "findings": ng_count, "ncCount": 1 if ng_count > 0 else 0}

def extract_audit():
    audit_dir = BASE / "9 內部稽核管理程序" / "記錄" / "內部稽核114年度"
    entries = []

    # 114年度第一次稽核（9.5 稽核報告書 — 2025/09/04）
    p95 = audit_dir / "9.5 品質稽核報告書.docx"
    if p95.exists():
        r = parse_audit_report(p95)
        if not r["date"]:
            r["date"] = "2025-09-04"
        entries.append({
            "id": "IA-2025-01",
            "year": 2025,
            "period": "下半年",
            "scheduledDate": "2025-09-04",
            "dept": r["dept"] or "全廠",
            "scope": "MP-01,MP-02,MP-03,MP-04,MP-05,MP-06",
            "auditor": r["auditor"] or "蔡有為",
            "auditee": "程鼎智",
            "status": "已完成",
            "actualDate": r["date"] or "2025-09-04",
            "findings": r["findings"] if r["findings"] else 4,
            "ncCount": 1,
        })
        print(f"  稽核 IA-2025-01: 日期={r['date']}, 稽核員={r['auditor']}", file=sys.stderr)

    # 114年度矯正通知單（9.4 — 2025/06/23，品管課）
    p94 = audit_dir / "9.4內部稽核矯正通知單.docx"
    if p94.exists():
        tables = read_tables(p94)
        date94 = dept94 = auditor94 = ""
        for tbl in tables:
            for row in tbl:
                joined = "".join(row)
                m = re.search(r"(\d{2,4})[./年](\d{1,2})[./月](\d{1,2})", joined)
                if m and not date94:
                    date94 = tw_date(m.group())
                if any(k in joined for k in ["品管課","生產課","管理部"]) and not dept94:
                    m2 = re.search(r"(品管課|生產課|管理部)", joined)
                    if m2:
                        dept94 = m2.group()
                if "稽核人員" in joined or "稽核員" in joined:
                    m3 = re.search(r"[：:]\s*(\S{2,4})", joined)
                    if m3 and not auditor94:
                        auditor94 = m3.group(1)
        entries.append({
            "id": "IA-2025-02",
            "year": 2025,
            "period": "上半年",
            "scheduledDate": "2025-06-23",
            "dept": dept94 or "品管課",
            "scope": "MP-11,MP-13",
            "auditor": auditor94 or "蔡有為",
            "auditee": "程鼎智",
            "status": "已完成",
            "actualDate": date94 or "2025-06-23",
            "findings": 1,
            "ncCount": 1,
        })
        print(f"  稽核 IA-2025-02: 日期={date94}, 部門={dept94}", file=sys.stderr)

    return entries

# ── JS 輸出工具 ────────────────────────────────────────────────────────────────

def to_js_obj(d, indent=2):
    sp = " " * indent
    items = []
    for k, v in d.items():
        if isinstance(v, list):
            if not v:
                items.append(f'{sp}{k}: []')
            elif isinstance(v[0], dict):
                inner = ",\n".join(to_js_obj(x, indent + 2) for x in v)
                items.append(f'{sp}{k}: [\n{inner}\n{sp}]')
            else:
                arr = ", ".join(f'"{js_str(x)}"' for x in v)
                items.append(f'{sp}{k}: [{arr}]')
        elif isinstance(v, bool):
            items.append(f'{sp}{k}: {"true" if v else "false"}')
        elif isinstance(v, int):
            items.append(f'{sp}{k}: {v}')
        elif isinstance(v, str):
            items.append(f'{sp}{k}: "{js_str(v)}"')
        else:
            items.append(f'{sp}{k}: null')
    inner = ",\n".join(items)
    return f"{{ {inner} }}"


# ── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    sep = "=" * 70

    print("\n" + sep)
    print("// ── initialTraining ─────────────────────────────────────────────────")
    print("// 來源：3 人力資源及訓練管理程序/記錄/3.4.X 教育訓練紀錄表(name).docx")
    training = extract_training()
    print("const initialTraining = [")
    for e in training:
        print(f"  {{ id: \"{e['id']}\", name: \"{js_str(e['name'])}\",")
        print(f"    dept: \"{js_str(e['dept'])}\", role: \"{js_str(e['role'])}\",")
        print(f"    hireDate: \"{e['hireDate']}\",")
        if e["trainings"]:
            print("    trainings: [")
            for t in e["trainings"]:
                print(f"      {{ course: \"{js_str(t['course'])}\", date: \"{t['date']}\",")
                print(f"        type: \"{t['type']}\", result: \"{t['result']}\", cert: \"{t['cert']}\" }},")
            print("    ]},")
        else:
            print("    trainings: [] },")
    print("];")

    print("\n" + sep)
    print("// ── initialEquipment ─────────────────────────────────────────────────")
    print("// 來源：4 設施設備管理程序/記錄/4.4.X潔沛設備維護履歷卡(name).docx")
    print("//       4 設施設備管理程序/記錄/4.5.1設施設備年度計劃表.docx")
    equipment = extract_equipment()
    print("const initialEquipment = [")
    for e in equipment:
        items_js = ", ".join(f'"{js_str(x)}"' for x in e["nextItems"])
        print(f"  {{ id: \"{e['id']}\", name: \"{js_str(e['name'])}\",")
        print(f"    location: \"{js_str(e['location'])}\",")
        print(f"    lastMaintenance: \"{e['lastMaintenance']}\",")
        print(f"    intervalDays: {e['intervalDays']},")
        print(f"    nextItems: [{items_js}] }},")
    print("];")

    print("\n" + sep)
    print("// ── initialSuppliers ─────────────────────────────────────────────────")
    print("// 來源：10 採購及供應商管理程序/記錄/10.3.X供應商定期評鑑表(name).docx")
    suppliers = extract_suppliers()
    print("const initialSuppliers = [")
    for s in suppliers:
        issues_js = ", ".join(f'"{js_str(x)}"' for x in s["issues"])
        print(f"  {{ id: \"{s['id']}\", name: \"{js_str(s['name'])}\",")
        print(f"    category: \"{js_str(s['category'])}\", contact: \"{js_str(s['contact'])}\",")
        print(f"    lastEvalDate: \"{s['lastEvalDate']}\", evalScore: {s['evalScore']},")
        print(f"    evalResult: \"{s['evalResult']}\", evalIntervalDays: {s['evalIntervalDays']},")
        print(f"    issues: [{issues_js}] }},")
    print("];")

    print("\n" + sep)
    print("// ── initialNonConformances ───────────────────────────────────────────")
    print("// 來源：15 不符合及矯正措施管理程序/記錄/15.1.1~15.1.2不符合報告表.docx")
    ncs = extract_nc()
    print("const initialNonConformances = [")
    for n in ncs:
        print(f"  {{ id: \"{n['id']}\", date: \"{n['date']}\",")
        print(f"    dept: \"{js_str(n['dept'])}\", type: \"{js_str(n['type'])}\",")
        print(f"    description: \"{js_str(n['description'])}\",")
        print(f"    severity: \"{n['severity']}\",")
        print(f"    rootCause: \"{js_str(n['rootCause'])}\",")
        print(f"    correctiveAction: \"{js_str(n['correctiveAction'])}\",")
        print(f"    responsible: \"{js_str(n['responsible'])}\",")
        print(f"    dueDate: \"{n['dueDate']}\", status: \"{n['status']}\",")
        print(f"    closeDate: \"{n['closeDate']}\", effectiveness: \"{n['effectiveness']}\" }},")
    print("];")

    print("\n" + sep)
    print("// ── initialAuditPlans ────────────────────────────────────────────────")
    print("// 來源：9 內部稽核管理程序/記錄/內部稽核114年度/9.4、9.5.docx")
    audits = extract_audit()
    print("const initialAuditPlans = [")
    for a in audits:
        print(f"  {{ id: \"{a['id']}\", year: {a['year']}, period: \"{a['period']}\",")
        print(f"    scheduledDate: \"{a['scheduledDate']}\",")
        print(f"    dept: \"{js_str(a['dept'])}\", scope: \"{a['scope']}\",")
        print(f"    auditor: \"{js_str(a['auditor'])}\", auditee: \"{js_str(a['auditee'])}\",")
        print(f"    status: \"{a['status']}\", actualDate: \"{a['actualDate']}\",")
        print(f"    findings: {a['findings']}, ncCount: {a['ncCount']} }},")
    print("];")

    print("\n" + sep)
    print("// ── initialEnvRecords ────────────────────────────────────────────────")
    print("// 查無 6 工作環境管理程序/記錄/ 下的實際環境監測紀錄 → 清空")
    print("const initialEnvRecords = [];")
