import os
import sys
import importlib
from typing import List

def check_file(path: str) -> bool:
    exists = os.path.exists(path)
    status = "OK" if exists else "FAIL"
    print(f"[{status}] {path}")
    return exists

def check_import(module_name: str) -> bool:
    try:
        # Add current directory to path if not already there
        if os.getcwd() not in sys.path:
            sys.path.append(os.getcwd())
        
        importlib.import_module(module_name)
        print(f"[OK] Import: {module_name}")
        return True
    except Exception as e:
        print(f"[FAIL] Import: {module_name} -> {e}")
        return False

def verify_system_v13():
    print("--- Sovereign AGI [Phase 13.04] MULTI-MODULAR INTEGRITY CHECK ---")
    
    critical_dirs = [
        "apps",
        "services",
        "libs",
        "workers",
        "agents",
        "libs/vendor/deer-flow"
    ]
    
    critical_files = [
        "libs/db/session.py",
        "libs/infra/lifespan.py",
        "services/orchestration/application/sovereign_cortex.py",
        "apps/public_api/main.py",
        ".env",
        "docker-compose.yml"
    ]
    
    print("\n[SECTION 1: Directory & File Checks]")
    all_ok = True
    for d in critical_dirs:
        if not check_file(d):
            all_ok = False
            
    for f in critical_files:
        if not check_file(f):
            all_ok = False
            
    print("\n[SECTION 2: Core Module Imports]")
    modules = [
        "libs.db.session",
        "libs.infra.lifespan",
        "services.orchestration.application.sovereign_cortex",
        "apps.public_api.main"
    ]
    for m in modules:
        if not check_import(m):
            all_ok = False

    print("\n--- SUMMARY ---")
    if all_ok:
        print("SYSTEM STATE: [HEALTHY] (Phase 13.04 Compliant)")
        sys.exit(0)
    else:
        print("SYSTEM STATE: [DEGRADED] (Missing Critical components)")
        sys.exit(1)

if __name__ == "__main__":
    verify_system_v13()
