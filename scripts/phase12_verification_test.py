
import sys
import os
from unittest.mock import MagicMock, patch, AsyncMock

# Environment setup
sys.path.append(os.getcwd())

async def test_audit_gate_logic():
    print("[TEST] AuditGate Multi-Model Census Testi Başlatılıyor...")
    
    # AuditGate import (updated code)
    from packages.orchestration.agi.security.audit_gate import AuditGate
    
    # Mock model orchestrator to simulate consensus
    mock_orch = AsyncMock()
    # Simulate 3 models agreeing
    mock_response = MagicMock(content='{"decision": "safe", "reason": "Test approval", "confidence": 0.98}')
    mock_orch.complete_task.return_value = mock_response
    
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        audit = AuditGate(model_orch=mock_orch)
        
        # Test high risk file
        result = await audit.verify_self_patch(
            file_path="packages/orchestration/agi/security/audit_gate.py", # High risk
            new_content="print('updated content')",
            reason="Security hardening"
        )
    
    print(f"[RESULT] Audit Result: {'SUCCESS' if result else 'FAILURE'}")
    assert result is True, "AuditGate should approve consensus-backed patch"
    
    # Verify GitService hook (optional check if it exists)
    from packages.orchestration.agi.operational.git_service import git_service
    print(f"[TEST] GitService Initialization: {'OK' if git_service else 'FAILED'}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_audit_gate_logic())
