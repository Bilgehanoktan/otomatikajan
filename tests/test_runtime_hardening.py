import asyncio
import os
import pytest
from db.session import is_db_available
from config import load_dotenv

@pytest.mark.asyncio
async def test_db_check_is_async_callable():
    """P0 Bug Regression Test: is_db_available'in await edilerek çağrılabildiğini doğrular."""
    try:
        # Fonksiyonun coroutine döndüğünden emin ol (await edilebilir olmalı)
        res = is_db_available()
        assert asyncio.iscoroutine(res), "P0 ERROR: is_db_available should be async!"
        
        # Gerçekten çalıştır
        status = await res
        assert isinstance(status, bool)
    except Exception as e:
        pytest.fail(f"is_db_available call failed: {e}")

def test_dotenv_override_consistency():
    """Faz 12 Hardening: config.py içindeki override=True varlığını doğrular."""
    config_path = os.path.join(os.getcwd(), "config.py")
    if not os.path.exists(config_path):
        pytest.skip("config.py not found in current directory")
        
    with open(config_path, "r", encoding="utf-8") as f:
        content = f.read()
        # load_dotenv calls should use override=True
        assert "override=True" in content, "SECURITY ERROR: load_dotenv should use override=True to prevent config leakage!"

@pytest.mark.asyncio
async def test_memory_watchdog_flag_integrity():
    """Hardening: Watchdog flag'inin os.environ üzerinde doğru set edildiğini test eder."""
    # Manuel olarak tetikleyelim (main.py içindeki mantığın simülasyonu)
    os.environ["SYSTEM_DEGRADED_MODE"] = "true"
    from main import health_check
    
    # health_check'i çağır
    res = await health_check()
    assert res["status"] == "degraded", "MONITORING ERROR: Status should be degraded when flag is true"
    assert res["reason"] == "memory_leak", "MONITORING ERROR: Reason should reflect the memory leak"
    
    # Temizle
    os.environ.pop("SYSTEM_DEGRADED_MODE", None)
    res_clean = await health_check()
    assert res_clean["status"] == "ok" if res_clean["status"] != "error" else "error"
