
import sys
from pathlib import Path
import os

# Project root path
ROOT_DIR = str(Path(__file__).resolve().parents[3])
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from fastapi import FastAPI
from apps.public_api.main import app

def print_routes(router, prefix=""):
    for route in router.routes:
        if hasattr(route, "path"):
            methods = getattr(route, "methods", [])
            print(f"{prefix}{route.path} [{','.join(methods)}]")
        elif hasattr(route, "app") and hasattr(route.app, "routes"):
            print_routes(route.app, prefix=prefix + route.path)
        else:
            print(f"{prefix}{route.path} [MOUNT]")

print_routes(app)
