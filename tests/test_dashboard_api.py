import re
import os
import pytest

# ── Helpers ───────────────────────────────────────────────

def get_router_files():
    return [
        "api/repair_router.py",
        "api/repair_admin_router.py",
        "api/faz12_router.py",
        "api/task_read_router.py",
        "api/task_write_router.py",
        "api/task_control_router.py",
        "api/monitoring_router.py",
        "api/specialists_router.py",
        "api/ceo_router.py",
        "api/self_update_router.py",
    ]

def load_endpoints(file_path):
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        src = f.read()
    # Matches @router.get/post/put/delete("...")
    return re.findall(r'@router\.(get|post|put|delete)\("([^"]+)"', src)

def normalize_ep(ep: str) -> str:
    """Normalize path parameters {param} -> * for comparison."""
    return re.sub(r'\{[^}]+\}', '*', ep)

# ── Tests ─────────────────────────────────────────────────

@pytest.mark.parametrize("router_file", get_router_files())
def test_router_file_exists(router_file):
    assert os.path.exists(router_file), f"{router_file} is missing"

def test_repair_critical_endpoints():
    endpoints = load_endpoints("api/repair_router.py")
    normalized_eps = [normalize_ep(ep) for _, ep in endpoints]
    
    required = [
        "/incidents",
        "/jobs",
        "/jobs/*/diff",
        "/jobs/*/validation",
        "/jobs/*/report",
        "/proposals",
        "/proposals/*/decision",
    ]
    
    for req in required:
        assert req in normalized_eps, f"Missing critical repair endpoint: {req}"

def test_faz12_critical_endpoints():
    endpoints = load_endpoints("api/faz12_router.py")
    normalized_eps = [normalize_ep(ep) for _, ep in endpoints]
    
    required = [
        "/debate/run",
        "/debate/personas",
        "/sandbox/run",
        "/model-router/route",
        "/vector-lessons/search",
    ]
    
    for req in required:
        assert req in normalized_eps, f"Missing critical Faz12 endpoint: {req}"

def test_dashboard_base_urls():
    # After refactor, these are in feature_app_v2.js
    js_path = os.path.join("dashboard", "feature_app_v2.js")
    assert os.path.exists(js_path)
    
    with open(js_path, "r", encoding="utf-8") as f:
        src = f.read()
    
    base_vars = dict(re.findall(r"const (BASE_\w+)\s*=\s*'([^']+)'", src))
    
    # Updated expectations after Faz 12 Spine Restoration
    expected = {
        "BASE_REPAIR": "/repair",
        "BASE_ADMIN":  "/repair/admin",
        "BASE_FAZ12":  "/faz12",
    }
    
    for var, val in expected.items():
        assert base_vars.get(var) == val, f"Dashboard mismatch for {var}: expected {val}, got {base_vars.get(var)}"

def test_main_router_inclusions():
    main_path = "main.py"
    assert os.path.exists(main_path)
    
    with open(main_path, "r", encoding="utf-8") as f:
        src = f.read()
    
    required_routers = [
        "repair_router",
        "repair_admin_router",
        "faz12_router",
        "task_read_router",
        "task_write_router",
        "self_update_router",
    ]
    
    for r in required_routers:
        # Modüler yapı kontrolü
        assert "register_routers(app)" in src
        
        # startup/routers.py kontrolü
        with open("startup/routers.py", "r", encoding="utf-8") as fs:
            routers_src = fs.read()
            assert f"include_router({r}" in routers_src, f"Router {r} not included in startup/routers.py"

def test_self_update_contract():
    """Verify self-update path and method in dashboard vs backend."""
    # After refactor, these are in feature_app_v2.js and core_app_v2.js
    core_path = "dashboard/core_app_v2.js"
    feat_path = "dashboard/feature_app_v2.js"
    
    src = ""
    if os.path.exists(core_path):
        with open(core_path, "r", encoding="utf-8") as f:
            src += f.read()
    if os.path.exists(feat_path):
        with open(feat_path, "r", encoding="utf-8") as f:
            src += f.read()
    
    # Check if dashboard uses the corrected path
    # Self-update artık startup/routers.py içinde
    with open("startup/routers.py", "r", encoding="utf-8") as fs:
        routers_src = fs.read()
        assert "self_update_router" in routers_src
    assert "/self-update/apply" in src or "/self-update" in src
    
    # Check backend router
    endpoints = load_endpoints("api/self_update_router.py")
    paths = [ep for _, ep in endpoints]
    assert "/state" in paths
    assert "/apply" in paths
