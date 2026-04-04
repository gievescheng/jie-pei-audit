#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""測試：匯入 `v2_backend/llm_service.py` 並建立 connector（不做 live 呼叫）"""
import importlib.util
from pathlib import Path

service_path = Path(__file__).resolve().parent.parent / "v2_backend" / "llm_service.py"
if not service_path.exists():
    raise SystemExit(f"找不到 {service_path}")

spec = importlib.util.spec_from_file_location("v2_backend.llm_service", str(service_path))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

print("HAS_get_connector=", hasattr(module, "get_connector_from_cfg"))
try:
    conn = module.get_connector_from_cfg()
    print("INSTANCE=", type(conn).__name__, "kwargs=", getattr(conn, "kwargs", None))
    print("IMPORT_TEST_OK")
except Exception as e:
    print("IMPORT_TEST_FAIL", type(e).__name__, e)
    raise
