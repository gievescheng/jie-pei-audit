# -*- coding: utf-8 -*-
"""
批量將 .doc 轉換為 .docx
使用 Microsoft Word COM 自動化
"""

import os
import sys
import glob
import time
import win32com.client

# 強制輸出使用 UTF-8（解決 Windows cp950 終端機問題）
sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = r'C:\Users\USER\Desktop\自動稽核程式'
DOCX_FORMAT = 16   # wdFormatXMLDocument = 16

def find_doc_files(base):
    """找出所有真正的 .doc 檔案（排除 .docx 和暫存 ~$ 檔）"""
    all_docs = glob.glob(os.path.join(base, '**', '*.doc'), recursive=True)
    return [
        f for f in all_docs
        if not f.lower().endswith('.docx')
        and not os.path.basename(f).startswith('~')
    ]

def convert_all():
    docs = find_doc_files(BASE_DIR)
    total = len(docs)

    if total == 0:
        print("找不到任何 .doc 檔案。")
        return

    print(f"找到 {total} 個 .doc 檔案，開始轉換...\n")

    # 開啟 Word（背景執行，不顯示視窗）
    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    word.DisplayAlerts = False

    ok = 0
    skip = 0
    fail = 0
    fail_list = []

    try:
        for idx, src_path in enumerate(docs, 1):
            dst_path = src_path + 'x'   # .doc → .docx

            # 若 .docx 已存在則跳過
            if os.path.exists(dst_path):
                print(f"[{idx:3}/{total}] 跳過（已存在）: {os.path.basename(dst_path)}")
                skip += 1
                continue

            try:
                doc = word.Documents.Open(
                    src_path,
                    ReadOnly=True,
                    AddToRecentFiles=False,
                    Visible=False
                )
                doc.SaveAs2(dst_path, FileFormat=DOCX_FORMAT)
                doc.Close(SaveChanges=False)
                ok += 1
                print(f"[{idx:3}/{total}] OK  {os.path.basename(dst_path)}")
            except Exception as e:
                fail += 1
                fail_list.append((os.path.basename(src_path), str(e)))
                print(f"[{idx:3}/{total}] ERR {os.path.basename(src_path)} -- {e}")

    finally:
        word.Quit()

    print(f"\n{'='*50}")
    print(f"完成！  成功: {ok}  跳過: {skip}  失敗: {fail}")
    if fail_list:
        print("\n失敗清單：")
        for name, err in fail_list:
            print(f"  {name}: {err}")

if __name__ == '__main__':
    t0 = time.time()
    convert_all()
    print(f"總耗時: {time.time()-t0:.1f} 秒")
