from __future__ import annotations

from fastapi import FastAPI

from .api.v1.router import router

app = FastAPI(title="JEPE ERP-QMS Core", version="0.2.0")
app.include_router(router)
