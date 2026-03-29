import os
import pytest

def test_router_files_exist():
    """Verify that all required router files exist on disk (Static Contract)."""
    required_routers = [
        "api/repair_router.py",
        "api/faz12_router.py",
        "api/task_read_router.py",
        "api/task_write_router.py",
        "api/improvement_router.py",
        "api/monitoring_router.py"
    ]
    for rf in required_routers:
        assert os.path.exists(rf), f"Missing router file: {rf}"

def test_main_includes_routers_static():
    """Verify that main.py includes all critical routers without importing it (Static Check)."""
    if not os.path.exists("main.py"):
        pytest.skip("main.py not found in current directory")
        
    with open("main.py", "r", encoding="utf-8") as f:
        src = f.read()
    
    critical_routers = [
        "repair_router",
        "faz12_router",
        "task_read_router",
        "task_write_router",
        "improvement_router",
        "monitoring_router"
    ]
    for router in critical_routers:
        # Modüler yapı kontrolü
        assert "register_routers(app)" in src
        
        with open("startup/routers.py", "r", encoding="utf-8") as fs:
            routers_src = fs.read()
            assert f"include_router({router}" in routers_src, f"Router {router} wiring check failed in startup/routers.py"

def test_improvement_router_admin_contract():
    """Verify that improvement_router has the required admin protection (Source Check)."""
    with open("api/improvement_router.py", "r", encoding="utf-8") as f:
        src = f.read()
    
    assert "require_admin" in src or "admin_only=True" in src, "Security contract mismatch: requirement_admin missing"
    assert '@router.get("/state"' in src, "Endpoint contract mismatch: /state missing"

def test_dashboard_api_prefix_alignment():
    """Verify dashboard points to the correct /api/v1 prefix."""
    # After refactor, this is in core_app.js
    js_path = os.path.join("dashboard", "core_app_v2.js")
    assert os.path.exists(js_path)
    with open(js_path, "r", encoding="utf-8") as f:
        src = f.read()
    assert "const API = '/api/v1'" in src or 'const API = "/api/v1"' in src
