import os
import pytest

def test_monitoring_status_aliasing_contract():
    """Verify that 'completed' -> 'done' and 'error' -> 'failed' mapping exists in API (Static Source Check)."""
    if not os.path.exists("api/monitoring_router.py"):
        pytest.skip("api/monitoring_router.py not found")
        
    with open("api/monitoring_router.py", "r", encoding="utf-8") as f:
        src = f.read()
    
    assert '"done":' in src, "Monitoring alias 'done' missing in source"
    assert '"failed":' in src, "Monitoring alias 'failed' missing in source"

def test_p1_05_header_contract():
    """Verify that X-System-Status header is included in middleware logic (Source Check)."""
    if not os.path.exists("observability/logging.py"):
        pytest.skip("observability/logging.py not found")
        
    with open("observability/logging.py", "r", encoding="utf-8") as f:
        src = f.read()
    
    assert "X-System-Status" in src, "X-System-Status contract missing in logging middleware"
    assert "await is_db_available()" in src, "await is_db_available() contract check missing or not awaited"

def test_hygiene_dot_env():
    """Verify that .env files are properly gitignored if possible."""
    if os.path.exists(".gitignore"):
        with open(".gitignore", "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
        
        # We check for general pattern or specific matching
        matches_env = any(".env" in l and not l.startswith("#") for l in lines)
        assert matches_env, ".env not safely gitignored in .gitignore"
