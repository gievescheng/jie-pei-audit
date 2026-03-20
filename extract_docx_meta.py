# -*- coding: utf-8 -*-
"""
掃描所有 .docx 檔案，讀取 DOCX 元資料，依路徑分類後更新 audit-dashboard.jsx
改良版：修正名稱回退邏輯、版本去重、revision 過大問題
"""

import os, zipfile, re, sys, json
from xml.etree import ElementTree as ET
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = r'C:\Users\USER\Desktop\自動稽核程式'
JSX_FILE  = os.path.join(BASE_DIR, 'audit-dashboard.jsx')

# ── 部門對應（依資料夾編號）────────────────────────────────────────────────
DEPT_MAP = {
    0: "管理部",  1: "管理部",  2: "管理部",  3: "管理部",
    4: "設備部",  5: "品管課",  6: "管理部",  7: "資訊部",
    8: "業務部",  9: "品管課", 10: "採購部", 11: "生產部",
    12: "品管課", 13: "品管課", 14: "倉儲部", 15: "品管課",
    16: "管理部"
}

# ── 程序書官方名稱（從資料夾名稱推導）────────────────────────────────────
PROC_OFFICIAL_NAME = {
    0:  "公司品質手冊",
    1:  "文件化資訊管制程序",
    2:  "組織環境與績效評估管理程序",
    3:  "人力資源及訓練管理程序",
    4:  "設施設備管理程序",
    5:  "量測資源管理程序",
    6:  "工作環境管理程序",
    7:  "資訊管理程序",
    8:  "客戶服務管理程序",
    9:  "內部稽核管理程序",
    10: "採購及供應商管理程序",
    11: "生產作業管理程序",
    12: "品質檢驗管理程序",
    13: "不合格品管制程序",
    14: "倉儲管理程序",
    15: "不符合及矯正措施管理程序",
    16: "管理審查程序",
}

# ── PDF 路徑對應（每個 MP 的現行 PDF）────────────────────────────────────
PROC_PDF = {
    0:  "0  品質手冊/公司品質手冊(2.0).pdf",
    1:  "",
    2:  "2 組織環境與績效管理程序/組織環境與績效評估管理程序(2.0).pdf",
    3:  "3 人力資源及訓練管理程序/人力資源及訓練管理程序.pdf",
    4:  "4 設施設備管理程序/設施設備管理程序2.0.pdf",
    5:  "5 量測資源管理程序/量測資源管理程序2.0.pdf",
    6:  "6 工作環境管理程序/工作環境管理程序(正式版).pdf",
    7:  "7 資訊管理程序/資訊管理程序2.0.pdf",
    8:  "8 客戶服務管理程序/客戶服務管理程序(4.0).pdf",
    9:  "9 內部稽核管理程序/內部稽核管理程序.pdf",
    10: "10 採購及供應商管理程序/採購及供應商管理程序(2.0).pdf",
    11: "11 生產作業管理程序/生產作業管理程序(2.0).pdf",
    12: "12 品質檢驗管理程序/品質檢驗管理程序3.0.pdf",
    13: "13 不合格品管制程序/不合格品管制程序.pdf",
    14: "14 倉儲管理程序/倉儲管理程序.pdf",
    15: "15 不符合及矯正措施管理程序/不符合及矯正措施管理程序2.0.pdf",
    16: "16 管理審查程序/管理審查程序.pdf",
}

NAMESPACES = {
    'cp':      'http://schemas.openxmlformats.org/package/2006/metadata/core-properties',
    'dc':      'http://purl.org/dc/elements/1.1/',
    'dcterms': 'http://purl.org/dc/terms/',
}

OBSOLETE_MARKERS = ['廢除', '舊版', '不要用', '要重印', '(不用)', '草稿', '(2) ']

def is_obsolete(fname):
    return any(m in fname for m in OBSOLETE_MARKERS)

def get_ver_from_name(fname):
    """從檔名括號或後綴提取版本號"""
    # 先試括號內版本如 (2.0)
    m = re.search(r'\((\d+(?:\.\d+)?)\)', fname)
    if m:
        try:
            return float(m.group(1))
        except:
            pass
    # 再試直接後綴如 2.0 或 3.0 在檔名末尾
    m = re.search(r'(\d+\.\d+)(?:\.docx)?$', fname, re.IGNORECASE)
    if m:
        try:
            v = float(m.group(1))
            if v < 20:   # 過大就不是版本號
                return v
        except:
            pass
    return 0.0

def get_base_name(fname):
    """
    從檔名提取「基底名稱」用於去重：
    去除 .docx、括號版本、後綴版本、尾端4位日期
    """
    s = re.sub(r'\.docx$', '', fname, flags=re.IGNORECASE)
    s = re.sub(r'\s*\([^)]*\)\s*', '', s)       # 去括號及內容
    s = re.sub(r'\s*\d+\.\d+\s*$', '', s)       # 去尾端 x.x 版本
    s = re.sub(r'\s*\d{4}\s*$', '', s)          # 去尾端4位日期(MMDD)
    return s.strip()

# ── 名稱清理：title 無效時回退用檔名 ─────────────────────────────────────
JUNK_TITLES = {'1', '0', '', 'untitled', 'document', 'new document', 'microsoft word - document'}

def is_junk_title(title):
    t = title.strip().lower()
    if not t or len(t) <= 2:
        return True
    if t in JUNK_TITLES or t.isdigit():
        return True
    # 外部公司名稱（去空格後比對，因 Word 表格常有間距）
    compact = title.replace(' ', '').replace('\u3000', '')
    if any(x in compact for x in ['股份有限公司', '有限公司']) and '潔沛' not in compact:
        return True
    # 作業指導書常見外來模板痕跡（短標題含外部廠商關鍵字）
    EXTERNAL_HINTS = ['群創', '日月光', '美光', '聯電', '友達', '奇美', 'XXX']
    if any(h in title for h in EXTERNAL_HINTS):
        return True
    return False

def derive_name_from_file(fname, cat=''):
    """從檔名推導顯示名稱"""
    name = re.sub(r'\.docx$', '', fname, flags=re.IGNORECASE)
    # 三階文件：移除 RW 前綴
    if cat == '作業指導書':
        name = re.sub(r'^RW[-_]?\d+[a-zA-Z]?\s*[-_]?\s*', '', name, flags=re.IGNORECASE).strip()
    return name if name else fname

def clean_name(title, fname, cat='', proc_num=None, is_primary=False):
    """
    決定最終顯示名稱：
    - 程序書首要版本 → 用官方名稱
    - title 有效 → 用 title
    - 否則 → 用檔名
    """
    if is_primary and proc_num is not None and proc_num in PROC_OFFICIAL_NAME:
        return PROC_OFFICIAL_NAME[proc_num]
    if not is_junk_title(title):
        # 正規化多餘空格（Word 表格常把文字間加空格）
        name = re.sub(r'\s{2,}', ' ', title.strip())
        name = re.sub(r'(?<=[\u4e00-\u9fff])\s(?=[\u4e00-\u9fff])', '', name)
        return name
    return derive_name_from_file(fname, cat)

# ── DOCX 元資料讀取 ───────────────────────────────────────────────────────
def read_docx_meta(path):
    try:
        with zipfile.ZipFile(path, 'r') as z:
            if 'docProps/core.xml' not in z.namelist():
                return {}
            with z.open('docProps/core.xml') as f:
                root = ET.parse(f).getroot()
                def g(ns_key, tag):
                    ns = NAMESPACES[ns_key]
                    e = root.find(f'{{{ns}}}{tag}')
                    return e.text.strip() if e is not None and e.text else ''

                title   = g('dc', 'title')
                creator = g('dc', 'creator')
                rev_str = g('cp', 'revision')
                created = g('dcterms', 'created') or g('dcterms', 'modified')

                dm = re.match(r'(\d{4}-\d{2}-\d{2})', created)
                date_str = dm.group(1) if dm else ''
                try:
                    rev = max(1, int(rev_str)) if rev_str else 1
                except:
                    rev = 1
                return {'title': title, 'creator': creator, 'rev': rev, 'date': date_str}
    except:
        return {}

def ver_str(rev, fname_ver):
    """決定版本字串：優先用檔名版本，revision > 10 視為編輯計數不用"""
    if fname_ver > 0 and fname_ver < 20:
        v = fname_ver
        return f"{int(v)}.0" if v == int(v) else str(v)
    if rev and 1 <= rev <= 10:
        return f"{rev}.0"
    return "1.0"

# ── 路徑分類 ──────────────────────────────────────────────────────────────
def classify(abs_path):
    """回傳 (cat, proc_num, dept) 或 None"""
    rel = os.path.relpath(abs_path, BASE_DIR).replace('\\', '/')
    parts = rel.split('/')
    if len(parts) < 2:
        return None

    top = parts[0]
    if top == '三階文件':
        return ('作業指導書', -1, '設備部')

    m = re.match(r'^(\d+)\s+', top)
    if not m:
        return None
    proc_num = int(m.group(1))
    dept = DEPT_MAP.get(proc_num, "管理部")

    if len(parts) == 2:
        cat = '管理手冊' if proc_num == 0 else '管理程序'
        return (cat, proc_num, dept)

    if len(parts) >= 3 and '表單' in parts[1]:
        return ('表單', proc_num, dept)
    if len(parts) >= 3 and '記錄' in parts[1]:
        return ('記錄', proc_num, dept)

    return None  # 深層子目錄暫不處理

# ── 掃描 ─────────────────────────────────────────────────────────────────
def scan():
    result = []
    for root_dir, dirs, files in os.walk(BASE_DIR):
        dirs[:] = [d for d in dirs if not d.startswith('.') and not d.startswith('~')]
        for fname in sorted(files):
            if not fname.lower().endswith('.docx') or fname.startswith('~'):
                continue
            if is_obsolete(fname):
                continue
            abs_path = os.path.join(root_dir, fname)
            info = classify(abs_path)
            if info is None:
                continue
            cat, proc_num, dept = info
            meta = read_docx_meta(abs_path)
            fv   = get_ver_from_name(fname)
            result.append({
                'abs_path': abs_path,
                'fname':    fname,
                'cat':      cat,
                'proc_num': proc_num,
                'dept':     dept,
                'title':    meta.get('title', ''),
                'creator':  meta.get('creator', ''),
                'rev':      meta.get('rev', 1),
                'date':     meta.get('date', ''),
                'fname_ver': fv,
                'base_name': get_base_name(fname),
            })
    return result

# ── 去重：同一資料夾、同基底名只保留最新版 ──────────────────────────────
def dedup_procedures(docs):
    """針對管理手冊/管理程序去重，其他類型全保留"""
    result = []
    proc_groups = defaultdict(list)

    for d in docs:
        if d['cat'] in ('管理手冊', '管理程序'):
            key = (d['proc_num'], d['base_name'])
            proc_groups[key].append(d)
        else:
            result.append(d)

    for key, group in proc_groups.items():
        # 取 fname_ver 最高者，tie-break 用 rev
        best = max(group, key=lambda x: (x['fname_ver'], x['rev']))
        result.append(best)

    return result

# ── 生成 JS ───────────────────────────────────────────────────────────────
def js_str(s):
    return json.dumps(s, ensure_ascii=False)

def build_js_arrays(docs):
    ORDER = {'管理手冊':0, '管理程序':1, '表單':2, '記錄':3, '作業指導書':4}
    docs.sort(key=lambda d: (ORDER.get(d['cat'],9), d['proc_num'], d['fname']))

    id_counter = defaultdict(int)
    rw_seen    = defaultdict(int)   # 用於重複 RW-XX ID

    lines_docs    = []
    lines_manuals = []

    for d in docs:
        cat      = d['cat']
        proc_num = d['proc_num']
        fv       = d['fname_ver']
        rev      = d['rev']
        creator  = d['creator']
        date_str = d['date']
        dept     = d['dept']
        fname    = d['fname']
        title    = d['title']
        v_str    = ver_str(rev, fv)
        rel_path = os.path.relpath(d['abs_path'], BASE_DIR).replace('\\', '/')

        # ── 決定 ID 與名稱 ──────────────────────────────────────────────
        if cat == '管理手冊':
            doc_id = 'MM-01'
            name   = clean_name(title, fname, cat, proc_num, is_primary=True)
            pdf_p  = PROC_PDF.get(0, '')

        elif cat == '管理程序':
            id_counter[('MP', proc_num)] += 1
            seq = id_counter[('MP', proc_num)]
            if seq == 1:
                doc_id = f'MP-{proc_num:02d}'
                name   = clean_name(title, fname, cat, proc_num, is_primary=True)
                pdf_p  = PROC_PDF.get(proc_num, '')
            else:
                suffix = chr(96 + seq)   # b, c, d ...
                doc_id = f'MP-{proc_num:02d}{suffix}'
                name   = clean_name(title, fname, cat, proc_num=None, is_primary=False)
                pdf_p  = ''

        elif cat == '表單':
            id_counter[('FR', proc_num)] += 1
            n = id_counter[('FR', proc_num)]
            doc_id = f'FR-{proc_num:02d}-{n:02d}'
            name   = clean_name(title, fname, cat)
            pdf_p  = ''

        elif cat == '記錄':
            id_counter[('RC', proc_num)] += 1
            n = id_counter[('RC', proc_num)]
            doc_id = f'RC-{proc_num:02d}-{n:02d}'
            name   = clean_name(title, fname, cat)
            pdf_p  = ''

        elif cat == '作業指導書':
            rw_m = re.match(r'RW[-_]?(\d+[a-zA-Z]?)', fname, re.IGNORECASE)
            if rw_m:
                rw_num = rw_m.group(1).upper()
            else:
                rw_num = 'X'
            rw_seen[rw_num] += 1
            if rw_seen[rw_num] == 1:
                doc_id = f'RW-{rw_num}'
            else:
                doc_id = f'RW-{rw_num}{chr(96 + rw_seen[rw_num])}'
            name  = clean_name(title, fname, cat)
            pdf_p = ''
        else:
            continue

        entry = (
            f'  {{ id:{js_str(doc_id)}, name:{js_str(name)}, '
            f'type:{js_str(cat)}, version:{js_str(v_str)}, '
            f'department:{js_str(dept)}, createdDate:{js_str(date_str)}, '
            f'author:{js_str(creator)}, retentionYears:16, '
            f'pdfPath:{js_str(pdf_p)}, docxPath:{js_str(rel_path)} }}'
        )

        if cat == '作業指導書':
            lines_manuals.append(entry)
        else:
            lines_docs.append(entry)

    # ── 補上原本只有 PDF 的設備手冊（無對應 .docx）─────────────────────
    existing_rw_ids = set()
    for l in lines_manuals:
        m = re.search(r'id:"([^"]+)"', l)
        if m:
            existing_rw_ids.add(m.group(1))

    PDF_ONLY = [
        # (id_candidate, name, dept, author, version, pdfPath)
        ("RW-01-PDF", "12吋 Wafer AOI 使用手冊",
         "品管課", "鏵友益電子", "1.0",
         "三階文件/RW01鏵友益_12inch Wafer AOI使用手冊_v1.0.pdf"),
        ("RW-02",     "12吋 Wafer Chipping AOI 使用手冊",
         "品管課", "鏵友益電子", "1.0",
         "三階文件/RW02鏵友益_12inch Wafer Chipping AOI使用手冊_v1.0(筛選機).pdf"),
        ("RW-09",     "空壓機 AM3-37A-E30 操作手冊",
         "設備部", "原廠商", "1.0",
         "三階文件/RW09空壓機AM3-37A-E30_Manual.pdf"),
        ("RW-10-PDF", "手持式微粒子計數器操作手冊",
         "品管課", "拓生科技", "1.0",
         "三階文件/RW10手持式微粒子計數器操作手冊 Model9303+軟體.pdf"),
        ("RW-11",     "玻璃晶圓 TTV 量測儀操作手冊",
         "品管課", "原廠商", "1.0",
         "三階文件/RW11玻璃晶圓否度量測專操作手冊_MSCF-C-0300(001)(真空產生器).pdf"),
    ]
    for (cand_id, name, dept, author, ver, pdf_p) in PDF_ONLY:
        # 若 ID 已存在則用 cand_id（已帶 -PDF 後綴，不會衝突）
        final_id = cand_id
        e = (
            f'  {{ id:{js_str(final_id)}, name:{js_str(name)}, '
            f'type:"作業指導書", version:{js_str(ver)}, '
            f'department:{js_str(dept)}, createdDate:"", '
            f'author:{js_str(author)}, retentionYears:16, '
            f'pdfPath:{js_str(pdf_p)}, docxPath:"" }}'
        )
        lines_manuals.append(e)

    return lines_docs, lines_manuals

# ── 主程式 ────────────────────────────────────────────────────────────────
def main():
    print("掃描 .docx 檔案...")
    raw = scan()
    print(f"  找到 {len(raw)} 個有效 .docx（排除廢止/草稿版）")

    deduped = dedup_procedures(raw)
    print(f"  去重後：{len(deduped)} 個")

    from collections import Counter
    cat_cnt = Counter(d['cat'] for d in deduped)
    for k in sorted(cat_cnt):
        print(f"    {k}: {cat_cnt[k]} 件")

    lines_docs, lines_manuals = build_js_arrays(deduped)

    # 輸出預覽 JS（前幾筆手冊+程序）
    print("\n=== 手冊/程序書預覽 ===")
    for l in lines_docs[:30]:
        print(l)

    print("\n=== 作業指導書預覽 ===")
    for l in lines_manuals:
        print(l)

    # 確認後再寫入 JSX
    print(f"\ninitialDocuments: {len(lines_docs)} 筆")
    print(f"initialManuals:   {len(lines_manuals)} 筆")

    # ── 更新 audit-dashboard.jsx ────────────────────────────────────────
    print("\n正在更新 audit-dashboard.jsx ...")
    with open(JSX_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    doc_start = doc_end = man_start = man_end = None
    for i, l in enumerate(lines):
        s = l.strip()
        if s.startswith('const initialDocuments') and doc_start is None:
            doc_start = i
        if doc_start is not None and doc_end is None and s == '];' and i > doc_start:
            doc_end = i
        if s.startswith('const initialManuals') and man_start is None:
            man_start = i
        if man_start is not None and man_end is None and s == '];' and i > man_start:
            man_end = i

    if any(x is None for x in [doc_start, doc_end, man_start, man_end]):
        print("ERROR: 找不到對應區塊，請確認 JSX 內容。")
        return

    print(f"  initialDocuments: 行 {doc_start+1}–{doc_end+1}")
    print(f"  initialManuals:   行 {man_start+1}–{man_end+1}")

    # 判斷 initialManuals 前是否有注釋行
    comment_line = man_start - 1
    has_comment = (comment_line >= 0 and
                   lines[comment_line].strip().startswith('//') and
                   '三階' in lines[comment_line])
    man_block_start = comment_line if has_comment else man_start

    new_docs_block = "const initialDocuments = [\n" + ",\n".join(lines_docs) + "\n];\n"
    new_man_block  = ("// 三階文件（設備手冊及作業指導書）\n"
                      "const initialManuals = [\n" +
                      ",\n".join(lines_manuals) + "\n];\n")

    new_lines = (
        lines[:doc_start] +
        [new_docs_block] +
        lines[doc_end+1:man_block_start] +
        [new_man_block] +
        lines[man_end+1:]
    )

    content = ''.join(new_lines)
    with open(JSX_FILE, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"  完成！audit-dashboard.jsx 現在 {content.count(chr(10))} 行")

    # ── 輸出 JS 預覽檔 ──────────────────────────────────────────────────
    out = r'C:\Users\USER\Desktop\docx_meta_output.js'
    with open(out, 'w', encoding='utf-8') as f:
        f.write("// initialDocuments\nconst initialDocuments = [\n")
        f.write(",\n".join(lines_docs))
        f.write("\n];\n\n// initialManuals\nconst initialManuals = [\n")
        f.write(",\n".join(lines_manuals))
        f.write("\n];\n")
    print(f"  預覽 JS 已輸出: {out}")

if __name__ == '__main__':
    main()
