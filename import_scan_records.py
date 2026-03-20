#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
import_scan_records.py
批量將電子掃描紀錄 PDF 建檔至稽核系統 initialDocuments

使用方式：
    python import_scan_records.py

執行後：
    1. 更新 index.html（在 initialDocuments 陣列插入新條目）
    2. 產生 patch_localStorage.js（貼入瀏覽器 F12 Console 立即生效）
"""

import os
import re
import json
import datetime

# ─────────────────────────────────────────────
# 路徑設定
# ─────────────────────────────────────────────
SCAN_BASE  = r'C:\Users\USER\Desktop\NAS\公用\ISO文件建立\潔沛修訂版\電子掃描紀錄'
INDEX_HTML = r'C:\Users\USER\Desktop\自動稽核程式\index.html'
INDEX_BASE = r'C:\Users\USER\Desktop\自動稽核程式'   # pdfPath 相對於此目錄
PATCH_JS   = r'C:\Users\USER\Desktop\自動稽核程式\patch_localStorage.js'

# ─────────────────────────────────────────────
# 程序資料夾 → 部門對照
# ─────────────────────────────────────────────
FOLDER_DEPT = {
    1:  "管理部",   # 文件化資訊管制程序
    2:  "管理部",   # 組織環境與績效管理程序
    3:  "管理部",   # 人力資源及訓練管理程序
    4:  "工程部",   # 設施設備管理程序
    5:  "品保課",   # 量測資源管理程序
    6:  "管理部",   # 工作環境管理程序
    7:  "管理部",   # 資訊管理程序
    8:  "業務部",   # 客戶服務管理程序
    9:  "管理部",   # 內部稽核管理程序
    10: "資材課",   # 採購及供應商管理程序
    11: "生產課",   # 生產作業管理程序
    12: "品保課",   # 品質檢驗管理程序
    13: "品保課",   # 不合格品管制程序
    14: "資材課",   # 倉儲管理程序
    15: "品保課",   # 不符合及矯正措施管理程序
    16: "管理部",   # 管理審查程序
}


# ─────────────────────────────────────────────
# 日期萃取
# ─────────────────────────────────────────────
def extract_date_from_filename(stem):
    """從檔名萃取日期（YYYYMMDD 或 YYYY-MM-DD 或 YYYY/MM/DD）"""
    m = re.search(r'(\d{4})[.\-/]?(\d{2})[.\-/]?(\d{2})', stem)
    if m:
        y, mo, d = int(m[1]), int(m[2]), int(m[3])
        if 2015 <= y <= 2035 and 1 <= mo <= 12 and 1 <= d <= 31:
            return f"{y:04d}-{mo:02d}-{d:02d}"
    return None


def extract_date_from_pdf(path):
    """嘗試用 pypdf 讀取 PDF 建立日期（需安裝 pypdf）"""
    try:
        from pypdf import PdfReader
        r = PdfReader(path)
        d_str = (r.metadata.get('/CreationDate') or '')
        m = re.match(r'D:(\d{4})(\d{2})(\d{2})', d_str)
        if m:
            return f"{m[1]}-{m[2]}-{m[3]}"
    except Exception:
        pass
    return None


def extract_date_from_mtime(path):
    """以檔案修改時間作為日期備援"""
    t = os.path.getmtime(path)
    dt = datetime.datetime.fromtimestamp(t)
    return dt.strftime('%Y-%m-%d')


def get_date(path, stem):
    """三層優先：檔名日期 → PDF 內嵌日期 → 修改時間"""
    d = extract_date_from_filename(stem)
    if d:
        return d
    d = extract_date_from_pdf(path)
    if d:
        return d
    return extract_date_from_mtime(path)


# ─────────────────────────────────────────────
# 解析 initialDocuments（去重用）
# ─────────────────────────────────────────────
def parse_existing_documents(html_content):
    """
    從 index.html 的 initialDocuments 區塊萃取現有 name 和 pdfPath。
    Returns: (set of names, set of pdfPaths)
    """
    m = re.search(r'const initialDocuments\s*=\s*\[', html_content)
    if not m:
        raise ValueError("找不到 const initialDocuments 區塊")

    # 找到 [ 的位置，追蹤括號深度找到對應的 ]
    bracket_start = html_content.index('[', m.start())
    depth = 0
    pos = bracket_start
    while pos < len(html_content):
        c = html_content[pos]
        if c == '[':
            depth += 1
        elif c == ']':
            depth -= 1
            if depth == 0:
                break
        pos += 1

    block = html_content[bracket_start:pos + 1]

    existing_names = set()
    existing_paths = set()
    for nm in re.finditer(r'name\s*:\s*"([^"]*)"', block):
        existing_names.add(nm.group(1).strip())
    for pp in re.finditer(r'pdfPath\s*:\s*"([^"]*)"', block):
        val = pp.group(1).strip()
        if val:
            existing_paths.add(val)

    return existing_names, existing_paths


def find_insert_position(html_content):
    """
    找到 initialDocuments 陣列結尾 ] 的字元索引，新條目將插入其前。
    """
    m = re.search(r'const initialDocuments\s*=\s*\[', html_content)
    if not m:
        raise ValueError("找不到 const initialDocuments 區塊")

    bracket_start = html_content.index('[', m.start())
    depth = 0
    pos = bracket_start
    while pos < len(html_content):
        c = html_content[pos]
        if c == '[':
            depth += 1
        elif c == ']':
            depth -= 1
            if depth == 0:
                return pos   # 在此 ] 之前插入
        pos += 1
    raise ValueError("找不到 initialDocuments 陣列的結束 ]")


# ─────────────────────────────────────────────
# 工具函式
# ─────────────────────────────────────────────
def js_escape(s):
    return s.replace('\\', '\\\\').replace('"', '\\"')


# ─────────────────────────────────────────────
# 主程式
# ─────────────────────────────────────────────
def main():
    print(f"讀取 {INDEX_HTML} ...")
    with open(INDEX_HTML, encoding='utf-8') as f:
        html_content = f.read()

    existing_names, existing_paths = parse_existing_documents(html_content)
    print(f"現有文件庫：{len(existing_names)} 個名稱、{len(existing_paths)} 個 PDF 路徑（去重基準）\n")

    new_entries = []
    skipped = 0
    errors = 0

    for folder_num in range(1, 17):
        # 找對應資料夾（以數字前綴比對）
        folder_dir = None
        for name in sorted(os.listdir(SCAN_BASE)):
            if re.match(rf'^{folder_num}\s', name) and \
               os.path.isdir(os.path.join(SCAN_BASE, name)):
                folder_dir = name
                break

        if folder_dir is None:
            print(f"  [WARN] 找不到資料夾 {folder_num}，跳過")
            continue

        folder_path = os.path.join(SCAN_BASE, folder_dir)
        dept = FOLDER_DEPT.get(folder_num, "管理部")
        seq = 0

        print(f">> 資料夾 {folder_num:02d}: {folder_dir}({dept})")

        # 遞迴蒐集 PDF（排序以確保順序一致）
        pdf_files = []
        for root, dirs, files in os.walk(folder_path):
            dirs.sort()
            for fn in sorted(files):
                if fn.lower().endswith('.pdf') and not fn.startswith('~$'):
                    pdf_files.append(os.path.join(root, fn))

        for pdf_path in pdf_files:
            try:
                fn   = os.path.basename(pdf_path)
                stem = os.path.splitext(fn)[0]

                # pdfPath：相對於 INDEX_BASE（即 ../NAS/...）
                rel = os.path.relpath(pdf_path, INDEX_BASE).replace('\\', '/')

                # 去重：名稱或路徑已存在則跳過
                if stem in existing_names:
                    print(f"    SKIP（名稱重複）: {fn}")
                    skipped += 1
                    continue
                if rel in existing_paths:
                    print(f"    SKIP（路徑重複）: {fn}")
                    skipped += 1
                    continue

                date_str = get_date(pdf_path, stem)
                seq += 1
                doc_id = f"REC-{folder_num:02d}-{seq:03d}"

                entry = {
                    'id':           doc_id,
                    'name':         stem,
                    'type':         '記錄',
                    'version':      '',
                    'department':   dept,
                    'createdDate':  date_str,
                    'author':       '',
                    'retentionYears': 10,
                    'pdfPath':      rel,
                    'docxPath':     '',
                }
                new_entries.append(entry)
                existing_names.add(stem)
                existing_paths.add(rel)
                print(f"    ADD {doc_id}: {fn}  [{date_str}]")

            except Exception as e:
                print(f"    ERROR: {pdf_path}: {e}")
                errors += 1

    print(f"\n{'='*60}")
    print(f"新增：{len(new_entries)} 筆  |  跳過（重複）：{skipped} 筆  |  錯誤：{errors} 筆")

    if not new_entries:
        print("無新增項目，結束。")
        return

    # ── 產生 JS 物件字串 ──
    js_lines = []
    for e in new_entries:
        line = (
            f'  {{ id:"{js_escape(e["id"])}", '
            f'name:"{js_escape(e["name"])}", '
            f'type:"{js_escape(e["type"])}", '
            f'version:"{js_escape(e["version"])}", '
            f'department:"{js_escape(e["department"])}", '
            f'createdDate:"{js_escape(e["createdDate"])}", '
            f'author:"{js_escape(e["author"])}", '
            f'retentionYears:{e["retentionYears"]}, '
            f'pdfPath:"{js_escape(e["pdfPath"])}", '
            f'docxPath:"{js_escape(e["docxPath"])}" }}'
        )
        js_lines.append(line)

    insert_str = ',\n'.join(js_lines) + ',\n'

    # ── 插入 index.html ──
    insert_pos = find_insert_position(html_content)
    new_html = html_content[:insert_pos] + insert_str + html_content[insert_pos:]

    with open(INDEX_HTML, encoding='utf-8', mode='w') as f:
        f.write(new_html)
    print(f"\n[OK] 已更新 {INDEX_HTML}")

    # ── 產生 patch_localStorage.js ──
    new_docs_json = json.dumps(new_entries, ensure_ascii=False, indent=2)

    patch_js = f"""// patch_localStorage.js
// 在瀏覽器 F12 → Console 頁籤貼上此腳本後按 Enter
// 將新增的電子掃描紀錄合併入文件庫，不清除現有資料
(function () {{
  const KEY = 'audit_documents';
  const newDocs = {new_docs_json};

  let existing = [];
  try {{ existing = JSON.parse(localStorage.getItem(KEY) || '[]'); }} catch (e) {{}}

  const existingNames = new Set(existing.map(d => d.name));
  const existingPaths = new Set(existing.map(d => d.pdfPath).filter(Boolean));

  let added = 0, skipped = 0;
  for (const doc of newDocs) {{
    if (existingNames.has(doc.name) || (doc.pdfPath && existingPaths.has(doc.pdfPath))) {{
      skipped++;
      continue;
    }}
    existing.push(doc);
    existingNames.add(doc.name);
    if (doc.pdfPath) existingPaths.add(doc.pdfPath);
    added++;
  }}

  localStorage.setItem(KEY, JSON.stringify(existing));
  console.log(`[OK] 完成：新增 ${{added}} 筆，跳過（重複）${{skipped}} 筆`);
  console.log(`文件庫現有 ${{existing.length}} 筆文件`);
}})();
"""

    with open(PATCH_JS, encoding='utf-8', mode='w') as f:
        f.write(patch_js)
    print(f"[OK] 已產生 {PATCH_JS}")

    print("\n=== 下一步（讓瀏覽器立即生效）===")
    print("1. 在瀏覽器開啟稽核系統（index.html）")
    print("2. 按 F12 → Console 頁籤")
    print("3. 複製 patch_localStorage.js 的全部內容，貼上後按 Enter")
    print("4. 重新整理頁面（F5），檢查文件管理頁籤")


if __name__ == '__main__':
    main()
