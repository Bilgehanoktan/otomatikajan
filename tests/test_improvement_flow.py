
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from core.improvement.gate import ImprovementGate

@pytest.mark.asyncio
async def test_improvement_gate_auto_apply():
    # Setup
    gate = ImprovementGate()
    
    mock_issue = {
        "type": "test_error",
        "agent_id": "test_agent",
        "reason": "Test reason",
        "evidence": {}
    }
    
    # Mock dependencies
    with patch("core.improvement.gate.observer") as mock_observer, \
         patch("core.improvement.gate.proposer") as mock_proposer, \
         patch("core.improvement.gate.verifier") as mock_verifier, \
         patch("core.orchestrator.orchestrator") as mock_orch, \
         patch("config.ENABLE_AUTONOMOUS_IMPROVEMENT", True), \
         patch("config.IMPROVEMENT_AUTO_APPLY_THRESHOLD", 0.5):
        
        mock_observer.scan_for_issues = AsyncMock(return_value=[mock_issue])
        mock_proposer.propose_fix = AsyncMock(return_value="print('fix')")
        mock_verifier.verify_patch = AsyncMock(return_value=True)
        
        mock_orch.self_updater = AsyncMock()
        mock_orch.ws_manager = AsyncMock()
        
        # Execute
        await gate.run_cycle()
        
        # Verify
        # 1. Proposer called
        mock_proposer.propose_fix.assert_called_once_with(mock_issue)
        # 2. Verifier called
        mock_verifier.verify_patch.assert_called_once()
        # 3. Self-updater called (auto-apply)
        mock_orch.self_updater.modify_system_file.assert_called_once()
        # 4. Reporting called
        mock_orch.ws_manager.broadcast.assert_called_once()
        
        print("\n[SUCCESS] Autonomous apply verified.")

@pytest.mark.asyncio
async def test_improvement_gate_manual_approval_needed():
    # Setup
    gate = ImprovementGate()
    
    mock_issue = {
        "type": "test_error",
        "agent_id": "test_agent",
        "reason": "Test reason",
        "evidence": {}
    }
    
    # Mock dependencies with auto-apply DISABLED
    with patch("core.improvement.gate.observer") as mock_observer, \
         patch("core.improvement.gate.proposer") as mock_proposer, \
         patch("core.improvement.gate.verifier") as mock_verifier, \
         patch("core.orchestrator.orchestrator") as mock_orch, \
         patch("config.ENABLE_AUTONOMOUS_IMPROVEMENT", False):
        
        mock_observer.scan_for_issues = AsyncMock(return_value=[mock_issue])
        mock_proposer.propose_fix = AsyncMock(return_value="print('fix')")
        mock_verifier.verify_patch = AsyncMock(return_value=True)
        
        mock_orch.self_updater = AsyncMock()
        
        # Execute
        await gate.run_cycle()
        
        # Verify
        # 1. Proposer called
        mock_proposer.propose_fix.assert_called_once_with(mock_issue)
        # 2. Self-updater NOT called
        mock_orch.self_updater.modify_system_file.assert_not_called()
        # 3. Added to active_proposals
        proposals = await gate.get_proposals()
        assert len(proposals) == 1
        assert proposals[0]["status"] == "pending_approval"
        
        print("\n[SUCCESS] Manual approval flow verified.")
