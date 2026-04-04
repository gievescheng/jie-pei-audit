#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""快速匯入測試：不執行網路呼叫，只驗證模組可載入與類別存在"""
import importlib.util
from pathlib import Path

file = Path(__file__).resolve().parent / "local_model_connector.py"
spec = importlib.util.spec_from_file_location("local_model_connector", str(file))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

print("HAS_LocalModelConnector=" + str(hasattr(module, "LocalModelConnector")))
# 嘗試建立實例（不呼叫 generate）
try:
    inst = module.LocalModelConnector(mode="http", base_url="http://localhost:1")
    print("INSTANCE_CREATED=True")
except Exception as e:
    print("INSTANCE_CREATED=False", type(e).__name__, e)
