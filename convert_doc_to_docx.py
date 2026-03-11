# -*- coding: utf-8 -*-
"""
批量將 .doc 轉換為 .docx 和 PDF
使用 Microsoft Word COM 自動化（需安裝 Microsoft Word）

目標資料夾：C:\\Users\\USER\\Desktop\\NAS\\公用\\ISO文件建立
輸出：每個 .doc 旁邊產生同名的 .docx 和 .pdf
原始 .doc 保留不刪除
"""

import os
import sys
import glob
import time
import win32com.client

# 強制輸出使用 UTF-8（解決 Windows cp950 終端機問題）
sys.stdout.reconfigure(encoding='utf-8')

# ── 設定 ──────────────────────────────────────────────────────────────────────
BASE_DIR = r'C:\Users\USER\Desktop\NAS\公用\ISO文件建立'
LOG_FILE = r'C:\Users\USER\Desktop\自動稽核程式\convert_log.txt'

DOCX_FORMAT = 16   # wdFormatXMLDocument
PDF_FORMAT  = 17   # wdFormatPDF


def find_doc_files(base):
    """找出所有真正的 .doc 檔案（排除 .docx 和暫存 ~$ 檔）"""
    all_docs = glob.glob(os.path.join(base, '**', '*.doc'), recursive=True)
    return sorted([
        f for f in all_docs
        if not f.lower().endswith('.docx')
        and not os.path.basename(f).startswith('~')
    ])


def convert_all():
    docs = find_doc_files(BASE_DIR)
    total = len(docs)

    if total == 0:
        print("找不到任何 .doc 檔案。")
        return

    # 統計需要實際轉換的數量（.docx 和 .pdf 皆已存在 → 跳過）
    need_convert = [
        f for f in docs
        if not (os.path.exists(f + 'x') and os.path.exists(f[:-4] + '.pdf'))
    ]
    print(f"找到 {total} 個 .doc 檔案")
    print(f"需要轉換（至少缺少 .docx 或 .pdf 之一）：{len(need_convert)} 個\n")

    # 開啟 Word（背景執行，不顯示視窗）
    print("啟動 Microsoft Word ...")
    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    word.DisplayAlerts = False

    ok = 0
    skip = 0
    fail = 0
    fail_list = []
    log_lines = []

    t0 = time.time()

    try:
        for idx, src_path in enumerate(docs, 1):
            dst_docx = src_path + 'x'                          # .doc → .docx
            dst_pdf  = os.path.splitext(src_path)[0] + '.pdf'  # .doc → .pdf
            basename = os.path.basename(src_path)

            has_docx = os.path.exists(dst_docx)
            has_pdf  = os.path.exists(dst_pdf)

            # 兩者皆已存在 → 完全跳過
            if has_docx and has_pdf:
                msg = f"[{idx:4}/{total}] 跳過（已存在）: {basename}"
                print(msg)
                log_lines.append(msg)
                skip += 1
                continue

            try:
                doc = word.Documents.Open(
                    src_path,
                    ReadOnly=True,
                    AddToRecentFiles=False,
                    Visible=False
                )

                # 存 .docx（若未存在）
                if not has_docx:
                    doc.SaveAs2(dst_docx, FileFormat=DOCX_FORMAT)

                # 存 PDF（若未存在）
                if not has_pdf:
                    doc.SaveAs2(dst_pdf, FileFormat=PDF_FORMAT)

                doc.Close(SaveChanges=False)
                ok += 1

                status = []
                if not has_docx: status.append('.docx')
                if not has_pdf:  status.append('.pdf')
                msg = f"[{idx:4}/{total}] OK  {basename}  →  {'+'.join(status)}"
                print(msg)
                log_lines.append(msg)

            except Exception as e:
                fail += 1
                fail_list.append((basename, str(e)))
                msg = f"[{idx:4}/{total}] ERR {basename} -- {e}"
                print(msg)
                log_lines.append(msg)

            # 每 50 個檔案印一次進度百分比
            if idx % 50 == 0:
                elapsed = time.time() - t0
                eta = elapsed / idx * (len(need_convert) - ok - fail)
                pct = idx / total * 100
                print(f"  ── 進度 {pct:.0f}%  耗時 {elapsed:.0f}s  預估剩餘 {eta:.0f}s ──")

    finally:
        word.Quit()

    elapsed = time.time() - t0
    summary = [
        '',
        '=' * 60,
        f'完成！  成功: {ok}  跳過: {skip}  失敗: {fail}  耗時: {elapsed:.0f} 秒',
        '=' * 60,
    ]
    if fail_list:
        summary.append('\n失敗清單：')
        for name, err in fail_list:
            summary.append(f'  {name}: {err}')

    for line in summary:
        print(line)
    log_lines.extend(summary)

    # 寫 log 檔
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write(f"轉換時間：{time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"目標目錄：{BASE_DIR}\n\n")
        f.write('\n'.join(log_lines))
    print(f"\nLog 已寫入：{LOG_FILE}")


if __name__ == '__main__':
    convert_all()
