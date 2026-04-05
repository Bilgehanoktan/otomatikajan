"""
Root main.py — Compatibility shim pointing to apps/api/main.py.
"""
import sys
from pathlib import Path

ROOT_DIR = str(Path(__file__).resolve().parent)
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from apps.api.main import app, APP_VERSION

if __name__ == "__main__":
    import uvicorn
    import os
    from config import PORT, HOST, DEBUG_LEVEL

    uvicorn.run(
        "main:app",
        host=HOST or "0.0.0.0",
        port=PORT or 8000,
        reload=(os.getenv("APP_ENV") == "development"),
        log_level=DEBUG_LEVEL.lower() if DEBUG_LEVEL else "info"
    )
