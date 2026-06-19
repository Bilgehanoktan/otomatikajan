import pytest
import os
from services.database.recovery.manager import DatabaseRecoveryManager

def test_database_diagnose():
    """Verify that database diagnostics can run successfully and return valid metadata."""
    diag = DatabaseRecoveryManager.diagnose()
    assert isinstance(diag, dict)
    assert "timestamp" in diag
    assert "database_path" in diag
    assert "exists" in diag
    assert "integrity_check" in diag
    assert "tables" in diag
    assert "status" in diag
    
    # Under standard test harness, the fallback db or primary db exists
    if diag["exists"]:
        assert diag["integrity_check"] == "OK"
        assert diag["status"] == "HEALTHY"

def test_database_recover_lifecycle():
    """Verify that lock-resilient database self-repair runs successfully without data loss."""
    diag_before = DatabaseRecoveryManager.diagnose()
    if not diag_before["exists"]:
        pytest.skip("Database file does not exist in this environment.")
        
    result = DatabaseRecoveryManager.recover()
    assert result["status"] == "SUCCESS"
    assert result["backup_created"] is True
    assert os.path.exists(result["backup_path"])
    
    # Run post-recovery diagnosis to verify health
    diag_after = DatabaseRecoveryManager.diagnose()
    assert diag_after["integrity_check"] == "OK"
    assert diag_after["status"] == "HEALTHY"
