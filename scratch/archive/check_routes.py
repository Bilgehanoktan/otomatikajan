
import sys
import os
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = str(Path(__file__).resolve().parents[1])
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from fastapi import FastAPI
from libs.infra.router_registry import register_routers

app = FastAPI()
register_routers(app)

print("Registered Routes:")
for route in app.routes:
    if hasattr(route, "path"):
        print(f"{route.path} [{', '.join(route.methods)}]")
