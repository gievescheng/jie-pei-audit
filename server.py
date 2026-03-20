from __future__ import annotations

import json
import os
import secrets
import tempfile
import time
import traceback
from pathlib import Path
from urllib.parse import urlencode

import requests
from flask import (
    Flask,
    Response,
    abort,
    jsonify,
    redirect,
    request,
    send_file,
    send_from_directory,
    session,
)
import ops_data
from runtime_paths import (
    GOOGLE_CONFIG_PATH,
    GOOGLE_TOKEN_PATH,
    get_or_create_flask_secret,
    migrate_legacy_private_files,
    public_root_contains_private_files,
)

BASE_DIR = Path(__file__).parent.resolve()
GOOGLE_AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_USERINFO_URL = 'https://www.googleapis.com/oauth2/v2/userinfo'
GOOGLE_CALENDAR_EVENTS_URL = 'https://www.googleapis.com/calendar/v3/calendars/primary/events'
GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
]
PUBLIC_STATIC_DIRS = {
    'vendor': BASE_DIR / 'vendor',
    'public': BASE_DIR / 'public',
}
PUBLIC_STATIC_FILES = {
    'index.html': BASE_DIR / 'index.html',
}

app = Flask(__name__, static_folder=None)
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024
migrate_legacy_private_files()
app.secret_key = os.environ.get('FLASK_SECRET_KEY') or get_or_create_flask_secret()


def read_json(path: Path, fallback):
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return fallback


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def delete_file(path: Path) -> None:
    if path.exists():
        path.unlink()


def load_google_config() -> dict:
    return read_json(GOOGLE_CONFIG_PATH, {})


def save_google_config(client_id: str, client_secret: str) -> dict:
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'updated_at': int(time.time()),
    }
    write_json(GOOGLE_CONFIG_PATH, data)
    return data


def clear_google_config() -> None:
    delete_file(GOOGLE_CONFIG_PATH)


def load_google_tokens() -> dict:
    return read_json(GOOGLE_TOKEN_PATH, {})


def save_google_tokens(tokens: dict) -> dict:
    tokens = dict(tokens)
    tokens['updated_at'] = int(time.time())
    write_json(GOOGLE_TOKEN_PATH, tokens)
    return tokens


def clear_google_tokens() -> None:
    delete_file(GOOGLE_TOKEN_PATH)


def google_redirect_uri() -> str:
    return request.host_url.rstrip('/') + '/api/google-calendar/oauth/callback'


def google_configured(config: dict | None = None) -> bool:
    config = config or load_google_config()
    return bool(config.get('client_id') and config.get('client_secret'))


def enrich_google_identity(tokens: dict) -> dict:
    access_token = tokens.get('access_token')
    if not access_token:
        return tokens
    try:
        response = requests.get(
            GOOGLE_USERINFO_URL,
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=20,
        )
        if response.ok:
            userinfo = response.json()
            tokens['email'] = userinfo.get('email', tokens.get('email', ''))
            tokens['name'] = userinfo.get('name', tokens.get('name', ''))
    except Exception:
        pass
    return tokens


def exchange_google_code(code: str, config: dict) -> dict:
    response = requests.post(
        GOOGLE_TOKEN_URL,
        data={
            'code': code,
            'client_id': config['client_id'],
            'client_secret': config['client_secret'],
            'redirect_uri': google_redirect_uri(),
            'grant_type': 'authorization_code',
        },
        timeout=20,
    )
    if not response.ok:
        raise RuntimeError(google_error_text(response))
    tokens = response.json()
    tokens['expires_at'] = int(time.time()) + int(tokens.get('expires_in', 3600)) - 60
    return enrich_google_identity(tokens)


def refresh_google_tokens(tokens: dict, config: dict) -> dict:
    expires_at = int(tokens.get('expires_at', 0) or 0)
    if expires_at > int(time.time()) + 30:
        return tokens

    refresh_token = tokens.get('refresh_token')
    if not refresh_token:
        raise RuntimeError('Google Calendar authorization expired. Please reconnect Google Calendar.')

    response = requests.post(
        GOOGLE_TOKEN_URL,
        data={
            'client_id': config['client_id'],
            'client_secret': config['client_secret'],
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token',
        },
        timeout=20,
    )
    if not response.ok:
        raise RuntimeError(google_error_text(response))

    refreshed = response.json()
    merged = dict(tokens)
    merged.update(refreshed)
    merged['refresh_token'] = refresh_token
    merged['expires_at'] = int(time.time()) + int(refreshed.get('expires_in', 3600)) - 60
    return save_google_tokens(enrich_google_identity(merged))


def require_google_access_token() -> tuple[str, dict]:
    config = load_google_config()
    if not google_configured(config):
        raise RuntimeError('Google Calendar is not configured. Fill in Client ID and Client Secret first.')

    tokens = load_google_tokens()
    if not tokens.get('access_token'):
        raise RuntimeError('Google Calendar is not connected. Complete Google authorization first.')

    tokens = refresh_google_tokens(tokens, config)
    return tokens['access_token'], tokens


def google_error_text(response: requests.Response) -> str:
    try:
        payload = response.json()
        if isinstance(payload.get('error'), dict):
            return payload['error'].get('message', json.dumps(payload, ensure_ascii=False))
        return payload.get('error_description') or payload.get('error') or json.dumps(payload, ensure_ascii=False)
    except Exception:
        return response.text.strip() or f'HTTP {response.status_code}'


def json_error(message: str, status_code: int = 400):
    return jsonify({'error': message}), status_code


def json_body() -> dict:
    return request.get_json(force=True) or {}


def save_ops_records(kind: str):
    body = json_body()
    records = body.get('records')
    replace_source_file = str(body.get('replace_source_file') or '').strip()
    if records is None:
        record = body.get('record')
        records = record if isinstance(record, list) else [record or body]
    if not isinstance(records, list) or not records:
        return json_error('No records provided.')
    items, saved = ops_data.upsert_records(
        kind,
        [record for record in records if isinstance(record, dict)],
        replace_source_file=replace_source_file,
    )
    payload = {'items': items, 'saved': saved}
    if kind == 'environment':
        payload['summary'] = ops_data.summarize_environment(items)
    return jsonify(payload)


def serve_managed_file(stored_path: str, as_attachment: bool):
    file_path = ops_data.get_serving_path(stored_path)
    if file_path is None:
        abort(404)
    return send_file(file_path, as_attachment=as_attachment, download_name=file_path.name)


def google_status_payload() -> dict:
    config = load_google_config()
    tokens = load_google_tokens()
    return {
        'configured': google_configured(config),
        'connected': bool(tokens.get('access_token')),
        'email': tokens.get('email', ''),
        'name': tokens.get('name', ''),
        'redirect_uri': google_redirect_uri(),
        'has_refresh_token': bool(tokens.get('refresh_token')),
        'expires_at': tokens.get('expires_at'),
    }


def build_event_payload(item: dict) -> dict:
    date_value = str(item.get('date', '')).strip()
    if len(date_value) != 10:
        raise ValueError('Each alert item must include a YYYY-MM-DD date.')

    title = str(item.get('title') or 'Audit reminder').strip()
    module = str(item.get('module') or '').strip()
    summary = str(item.get('summary') or '').strip()
    owner = str(item.get('owner') or '').strip()

    details = [
        f'Module: {module}' if module else '',
        f'Summary: {summary}' if summary else '',
        f'Owner: {owner}' if owner else '',
    ]
    return {
        'summary': title,
        'description': '\n'.join(line for line in details if line),
        'start': {'date': date_value},
        'end': {'date': add_days(date_value, 1)},
    }


def add_days(date_str: str, days: int) -> str:
    from datetime import date, timedelta

    base = date.fromisoformat(date_str)
    return (base + timedelta(days=days)).isoformat()


def resolve_public_static_file(filename: str) -> Path | None:
    cleaned = filename.strip().lstrip('/').replace('\\', '/')
    if not cleaned or cleaned.startswith('.'):
        return None
    if cleaned in PUBLIC_STATIC_FILES:
        path = PUBLIC_STATIC_FILES[cleaned]
        return path if path.exists() and path.is_file() else None

    for prefix, root in PUBLIC_STATIC_DIRS.items():
        if cleaned == prefix or not cleaned.startswith(prefix + '/'):
            continue
        relative = cleaned[len(prefix) + 1 :]
        candidate = (root / relative).resolve()
        try:
            candidate.relative_to(root.resolve())
        except ValueError:
            return None
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def startup_security_warnings(host: str) -> list[str]:
    warnings = []
    public_private_files = public_root_contains_private_files()
    if public_private_files:
        warnings.append('Private config files are still present in the public project root.')
    if host == '0.0.0.0':
        warnings.append('Server is bound to 0.0.0.0. Other machines on the network may reach this site.')
    if not os.environ.get('FLASK_SECRET_KEY'):
        warnings.append('FLASK_SECRET_KEY is not provided. Using a generated local secret file instead.')
    return warnings


@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'index.html')


@app.route('/<path:filename>')
def static_files(filename):
    filepath = resolve_public_static_file(filename)
    if filepath is not None:
        return send_from_directory(filepath.parent, filepath.name)
    abort(404)


@app.route('/api/files/view')
def api_view_file():
    return serve_managed_file(request.args.get('path', ''), as_attachment=False)


@app.route('/api/files/download')
def api_download_file():
    return serve_managed_file(request.args.get('path', ''), as_attachment=True)


@app.route('/api/files/preview-text')
def api_preview_text_file():
    html_payload = ops_data.build_text_preview_html(request.args.get('path', ''))
    if html_payload is None:
        abort(404)
    return Response(html_payload, mimetype='text/html')


@app.route('/api/nonconformances', methods=['GET'])
def api_nonconformances_list():
    return jsonify({'items': ops_data.load_records('nonconformance')})


@app.route('/api/nonconformances', methods=['POST'])
def api_nonconformances_save():
    try:
        return save_ops_records('nonconformance')
    except Exception as exc:
        traceback.print_exc()
        return json_error(str(exc), 500)


@app.route('/api/nonconformances/<record_id>', methods=['DELETE'])
def api_nonconformances_delete(record_id):
    try:
        items, deleted = ops_data.delete_record('nonconformance', record_id)
        if not deleted:
            return json_error('Record not found.', 404)
        return jsonify({'items': items, 'deleted_id': record_id})
    except Exception as exc:
        traceback.print_exc()
        return json_error(str(exc), 500)


@app.route('/api/nonconformances/import', methods=['POST'])
def api_nonconformances_import():
    try:
        upload = request.files.get('file')
        if upload is None or not upload.filename:
            return json_error('Upload file is required.')
        return jsonify(ops_data.parse_import('nonconformance', upload))
    except ValueError as exc:
        return json_error(str(exc), 400)
    except Exception as exc:
        traceback.print_exc()
        return json_error(str(exc), 500)


@app.route('/api/audit-plans', methods=['GET'])
def api_audit_plans_list():
    return jsonify({'items': ops_data.load_records('auditplan')})


@app.route('/api/audit-plans', methods=['POST'])
def api_audit_plans_save():
    try:
        return save_ops_records('auditplan')
    except Exception as exc:
        traceback.print_exc()
        return json_error(str(exc), 500)


@app.route('/api/audit-plans/<record_id>', methods=['DELETE'])
def api_audit_plans_delete(record_id):
    try:
        items, deleted = ops_data.delete_record('auditplan', record_id)
        if not deleted:
            return json_error('Record not found.', 404)
        return jsonify({'items': items, 'deleted_id': record_id})
    except Exception as exc:
        traceback.print_exc()
        return json_error(str(exc), 500)


@app.route('/api/audit-plans/import', methods=['POST'])
def api_audit_plans_import():
    try:
        upload = request.files.get('file')
        if upload is None or not upload.filename:
            return json_error('Upload file is required.')
        return jsonify(ops_data.parse_import('auditplan', upload))
    except ValueError as exc:
        return json_error(str(exc), 400)
    except Exception as exc:
        traceback.print_exc()
        return json_error(str(exc), 500)


@app.route('/api/audit-plans/<record_id>/attachments', methods=['GET'])
def api_audit_plan_attachments(record_id):
    try:
        return jsonify({'attachments': ops_data.list_auditplan_attachments(record_id)})
    except KeyError:
        return json_error('Record not found.', 404)
    except Exception as exc:
        traceback.print_exc()
        return json_error(str(exc), 500)


@app.route('/api/environment-records', methods=['GET'])
def api_environment_records_list():
    start = request.args.get('start', '')
    end = request.args.get('end', '')
    items = ops_data.filter_environment_records(start, end)
    return jsonify({'items': items, 'summary': ops_data.summarize_environment(items)})


@app.route('/api/environment-records', methods=['POST'])
def api_environment_records_save():
    try:
        return save_ops_records('environment')
    except Exception as exc:
        traceback.print_exc()
        return json_error(str(exc), 500)


@app.route('/api/environment-records/<record_id>', methods=['DELETE'])
def api_environment_records_delete(record_id):
    try:
        items, deleted = ops_data.delete_record('environment', record_id)
        if not deleted:
            return json_error('Record not found.', 404)
        return jsonify({'items': items, 'summary': ops_data.summarize_environment(items), 'deleted_id': record_id})
    except Exception as exc:
        traceback.print_exc()
        return json_error(str(exc), 500)


@app.route('/api/environment-records/import', methods=['POST'])
def api_environment_records_import():
    try:
        upload = request.files.get('file')
        if upload is None or not upload.filename:
            return json_error('Upload file is required.')
        return jsonify(ops_data.parse_import('environment', upload))
    except ValueError as exc:
        return json_error(str(exc), 400)
    except Exception as exc:
        traceback.print_exc()
        return json_error(str(exc), 500)


@app.route('/api/environment-records/delete-range', methods=['POST'])
def api_environment_records_delete_range():
    try:
        body = json_body()
        start = body.get('start', '')
        end = body.get('end', '')
        items, removed = ops_data.delete_environment_range(start, end)
        return jsonify({'items': items, 'summary': ops_data.summarize_environment(items), 'removed_count': removed, 'deleted': removed})
    except Exception as exc:
        traceback.print_exc()
        return json_error(str(exc), 500)


@app.route('/api/production-records/read-existing', methods=['GET'])
def api_production_records_read_existing():
    try:
        import record_imports

        records, source_file = record_imports.load_existing_production_records()
        return jsonify({'records': records, 'source_file': source_file})
    except Exception as exc:
        traceback.print_exc()
        return json_error(str(exc), 500)


@app.route('/api/quality-records/read-existing', methods=['GET'])
def api_quality_records_read_existing():
    try:
        import record_imports

        records, source_file = record_imports.load_existing_quality_records()
        return jsonify({'records': records, 'source_file': source_file})
    except Exception as exc:
        traceback.print_exc()
        return json_error(str(exc), 500)


@app.route('/api/generate', methods=['POST'])
def api_generate():
    try:
        import generate_record

        body = request.get_json(force=True)
        rec_type = body.get('type', '')
        data = body.get('data', [])

        if rec_type not in ('env', 'production', 'quality'):
            return jsonify({'error': f'Unsupported type: {rec_type}'}), 400

        tmp = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False, dir=tempfile.gettempdir())
        tmp.close()
        out_path = generate_record.run(rec_type, data, tmp.name)

        filenames = {
            'env': '環境監測記錄.xlsx',
            'production': '生產記錄.xlsx',
            'quality': '品質檢驗記錄.xlsx',
        }
        return send_file(
            out_path,
            as_attachment=True,
            download_name=filenames[rec_type],
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@app.route('/api/record-engine/catalog', methods=['GET'])
def api_record_engine_catalog():
    try:
        import record_engine

        return jsonify({'templates': record_engine.get_catalog()})
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@app.route('/api/record-engine/suggest', methods=['POST'])
def api_record_engine_suggest():
    try:
        import record_engine

        body = request.get_json(force=True) or {}
        prompt = body.get('prompt', '')
        context = body.get('context') or {}
        return jsonify({'templates': record_engine.suggest_templates(prompt, context)})
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@app.route('/api/record-engine/generate', methods=['POST'])
def api_record_engine_generate():
    try:
        import record_engine

        body = request.get_json(force=True) or {}
        out_path, download_name, mimetype = record_engine.generate_template(body)
        return send_file(
            str(out_path),
            as_attachment=True,
            download_name=download_name,
            mimetype=mimetype,
        )
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@app.route('/api/notion', methods=['POST'])
def api_notion():
    try:
        body = request.get_json(force=True)
        token = body.get('token', '').strip()
        db_id = body.get('db_id', '').strip()
        properties = body.get('properties', {})

        if not token or not db_id:
            return jsonify({'error': 'token and db_id are required.'}), 400

        response = requests.post(
            'https://api.notion.com/v1/pages',
            json={'parent': {'database_id': db_id}, 'properties': properties},
            headers={
                'Authorization': f'Bearer {token}',
                'Notion-Version': '2022-06-28',
                'Content-Type': 'application/json',
            },
            timeout=20,
        )
        return jsonify(response.json()), response.status_code
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@app.route('/api/shipment-draft/catalog', methods=['GET'])
def shipment_draft_catalog():
    try:
        import shipment_draft

        return jsonify({'orders': shipment_draft.get_order_catalog()})
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@app.route('/api/shipment-draft/generate', methods=['POST'])
def shipment_draft_generate():
    try:
        import shipment_draft

        body = request.get_json(force=True) or {}
        out_path, download_name = shipment_draft.build_shipment_draft(body)
        return send_file(
            out_path,
            as_attachment=True,
            download_name=download_name,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@app.route('/api/google-calendar/status', methods=['GET'])
def google_calendar_status():
    return jsonify(google_status_payload())


@app.route('/api/google-calendar/config', methods=['POST'])
def google_calendar_config():
    body = request.get_json(force=True) or {}
    if body.get('clear'):
        clear_google_config()
        clear_google_tokens()
        return jsonify(google_status_payload())

    client_id = body.get('client_id', '').strip()
    client_secret = body.get('client_secret', '').strip()
    if not client_id or not client_secret:
        return jsonify({'error': 'client_id and client_secret are required.'}), 400

    save_google_config(client_id, client_secret)
    clear_google_tokens()
    return jsonify(google_status_payload())


@app.route('/api/google-calendar/auth/start', methods=['GET'])
def google_calendar_auth_start():
    config = load_google_config()
    if not google_configured(config):
        return jsonify({'error': 'Google Calendar is not configured yet.'}), 400

    state = secrets.token_urlsafe(24)
    session['google_oauth_state'] = state
    auth_url = GOOGLE_AUTH_URL + '?' + urlencode({
        'client_id': config['client_id'],
        'redirect_uri': google_redirect_uri(),
        'response_type': 'code',
        'scope': ' '.join(GOOGLE_SCOPES),
        'access_type': 'offline',
        'prompt': 'consent',
        'include_granted_scopes': 'true',
        'state': state,
    })
    return jsonify({'auth_url': auth_url, 'redirect_uri': google_redirect_uri()})


@app.route('/api/google-calendar/oauth/callback', methods=['GET'])
def google_calendar_oauth_callback():
    expected_state = session.get('google_oauth_state')
    incoming_state = request.args.get('state', '')
    if not expected_state or expected_state != incoming_state:
        return redirect('/?google=error&reason=state')

    if request.args.get('error'):
        return redirect('/?google=error&reason=' + request.args.get('error', 'oauth'))

    code = request.args.get('code', '')
    if not code:
        return redirect('/?google=error&reason=missing_code')

    try:
        config = load_google_config()
        tokens = exchange_google_code(code, config)
        save_google_tokens(tokens)
        session.pop('google_oauth_state', None)
        return redirect('/?google=connected')
    except Exception:
        traceback.print_exc()
        return redirect('/?google=error&reason=token_exchange')


@app.route('/api/google-calendar/events', methods=['POST'])
def google_calendar_events():
    try:
        body = request.get_json(force=True) or {}
        items = body.get('items')
        if items is None:
            items = [body]
        if not isinstance(items, list) or not items:
            return jsonify({'error': 'items must be a non-empty array.'}), 400

        access_token, tokens = require_google_access_token()
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
        }

        results = []
        success_count = 0
        for item in items:
            try:
                payload = build_event_payload(item)
                response = requests.post(GOOGLE_CALENDAR_EVENTS_URL, json=payload, headers=headers, timeout=20)
                if not response.ok:
                    raise RuntimeError(google_error_text(response))
                event = response.json()
                results.append({
                    'title': item.get('title', ''),
                    'success': True,
                    'event_id': event.get('id', ''),
                    'html_link': event.get('htmlLink', ''),
                })
                success_count += 1
            except Exception as exc:
                results.append({
                    'title': item.get('title', ''),
                    'success': False,
                    'error': str(exc),
                })

        failed_count = len(results) - success_count
        status_code = 200 if failed_count == 0 else 207
        return jsonify({
            'email': tokens.get('email', ''),
            'success_count': success_count,
            'failed_count': failed_count,
            'results': results,
        }), status_code
    except RuntimeError as exc:
        return jsonify({'error': str(exc)}), 400
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@app.route('/api/google-calendar/logout', methods=['POST'])
def google_calendar_logout():
    clear_google_tokens()
    return jsonify(google_status_payload())


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8888))
    host = os.environ.get('HOST', '127.0.0.1')
    print(f'[server] http://{host}:{port}')
    print(f'[base] {BASE_DIR}')
    for warning in startup_security_warnings(host):
        print(f'[security-warning] {warning}')
    app.run(host=host, port=port, debug=False, use_reloader=False)
