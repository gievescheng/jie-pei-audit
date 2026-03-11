"""
潔沛企業 ISO 9001:2015 稽核系統 — Flask 伺服器
取代 python -m http.server 8888，同時提供：
  GET  /              → index.html
  GET  /<path>        → 靜態檔案（XLSX, DOCX, PDF…）
  POST /api/generate  → 呼叫 generate_record.py，回傳填好的 XLSX
  POST /api/notion    → 代理 Notion API（解決 CORS 限制）

啟動方式：
  python server.py
  （預設 port 8888，可用環境變數 PORT 覆蓋）
"""

import os
import sys
import json
import tempfile
import traceback
from pathlib import Path

from flask import (
    Flask, request, jsonify, send_file,
    send_from_directory, abort
)

# ── 基礎路徑 ───────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.resolve()

app = Flask(__name__, static_folder=str(BASE_DIR))
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024  # 64 MB 上傳上限


# ════════════════════════════════════════════════════════════
# 靜態資源服務
# ════════════════════════════════════════════════════════════

@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'index.html')


@app.route('/<path:filename>')
def static_files(filename):
    """服務目錄下所有靜態檔案（XLSX, DOCX, PDF, JS…）"""
    filepath = BASE_DIR / filename
    if filepath.exists() and filepath.is_file():
        return send_from_directory(BASE_DIR, filename)
    abort(404)


# ════════════════════════════════════════════════════════════
# API：生成記錄文件
# ════════════════════════════════════════════════════════════

@app.route('/api/generate', methods=['POST'])
def api_generate():
    """
    Request JSON:
      { "type": "env"|"production"|"quality",
        "data": [ {...}, ... ] }

    Response:
      XLSX 檔案（Content-Disposition: attachment）
    """
    try:
        import generate_record
        body = request.get_json(force=True)
        rec_type = body.get('type', '')
        data = body.get('data', [])

        if rec_type not in ('env', 'production', 'quality'):
            return jsonify({'error': f'未知 type: {rec_type}'}), 400

        # 生成暫存 XLSX
        tmp = tempfile.NamedTemporaryFile(
            suffix='.xlsx', delete=False,
            dir=tempfile.gettempdir()
        )
        tmp.close()
        out_path = generate_record.run(rec_type, data, tmp.name)

        filenames = {
            'env':        '環境監控記錄表_已填.xlsx',
            'production': '生產日報記錄表_已填.xlsx',
            'quality':    '品質管理記錄表_已填.xlsx',
        }
        return send_file(
            out_path,
            as_attachment=True,
            download_name=filenames[rec_type],
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ════════════════════════════════════════════════════════════
# API：Notion 代理
# ════════════════════════════════════════════════════════════

@app.route('/api/notion', methods=['POST'])
def api_notion():
    """
    Request JSON:
      { "token":  "<Notion Integration Token>",
        "db_id":  "<Database ID>",
        "properties": { ... Notion page properties ... } }

    Response:
      Notion API 回傳的 JSON
    """
    try:
        import requests as req_lib
        body = request.get_json(force=True)

        token = body.get('token', '').strip()
        db_id = body.get('db_id', '').strip()
        properties = body.get('properties', {})

        if not token or not db_id:
            return jsonify({'error': 'token 與 db_id 為必填'}), 400

        payload = {
            'parent': {'database_id': db_id},
            'properties': properties
        }
        headers = {
            'Authorization': f'Bearer {token}',
            'Notion-Version': '2022-06-28',
            'Content-Type': 'application/json'
        }
        r = req_lib.post(
            'https://api.notion.com/v1/pages',
            json=payload,
            headers=headers,
            timeout=15
        )
        return jsonify(r.json()), r.status_code

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ════════════════════════════════════════════════════════════
# 啟動
# ════════════════════════════════════════════════════════════

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8888))
    print(f'[潔沛稽核系統] Flask 伺服器啟動 → http://localhost:{port}')
    print(f'[目錄] {BASE_DIR}')
    # use_reloader=False 避免 Windows 下 double-spawn 問題
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
