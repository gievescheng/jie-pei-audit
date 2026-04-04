#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""測試：匯入 v2_backend.llm_routes 並檢查 llm_bp 存在"""
import importlib.util
from pathlib import Path

file = Path(__file__).resolve().parent.parent / "v2_backend" / "llm_routes.py"
spec = importlib.util.spec_from_file_location("v2_backend.llm_routes", str(file))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

print("HAS_llm_bp=", hasattr(module, "llm_bp"))
print("BP_NAME=", getattr(module, "llm_bp").name if hasattr(module, "llm_bp") else None)
