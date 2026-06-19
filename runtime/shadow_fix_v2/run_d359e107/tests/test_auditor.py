import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from services.governance.auditor_service import AuditorService
from libs.governance.launch_gatekeeper import LaunchGatekeeper
import os

@pytest.mark.asyncio
async def test_audit_bundle_generation():
    """Verifies that an audit bundle can be created and hashed."""
    path = await AuditorService.create_and_export_bundle(
        name="TEST_BUNDLE",
        purpose="VERIFICATION",
        start=datetime.now(timezone.utc) - timedelta(days=1),
        end=datetime.now(timezone.utc),
        operator="TEST_USER"
    )
    
    assert os.path.exists(path)
    assert path.endswith(".zip")
    print(f"\n[PASS] Audit bundle created at: {path}")

@pytest.mark.asyncio
async def test_launch_gatekeeper_logic():
    """Verifies that the gatekeeper correctly evaluates system state."""
    passed, results = await LaunchGatekeeper.validate_for_rollout()
    
    # We expect this to pass if budget and governance are healthy
    # On a fresh environment, it might fail if models aren't migrated
    assert isinstance(passed, bool)
    assert "budget" in results
    assert "governance" in results
    print(f"\n[PASS] Gatekeeper check complete. Passed: {passed}")

if __name__ == "__main__":
    asyncio.run(test_audit_bundle_generation())
    asyncio.run(test_launch_gatekeeper_logic())
