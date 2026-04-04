import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from core.improvement.autonomous_governor import AutonomousGovernor
from core.improvement.cognitive_verifier import CognitiveVerifier

@pytest.mark.asyncio
async def test_governor_cycle_with_cognitive_verifier():
    """
    AutonomousGovernor'ın CognitiveVerifier (DebateEngine) ile olan etkileşimini test eder.
    """
    # 1. Mock Observer & Proposer
    with patch("core.improvement.observer.observer.scan_for_issues", new_callable=AsyncMock) as mock_scan, \
         patch("core.improvement.proposer.proposer.propose_fix", new_callable=AsyncMock) as mock_propose:
        
        mock_scan.return_value = [{"reason": "memory_leak", "agent_id": "core/nexus.py"}]
        mock_propose.return_value = "patch content"
        
        # 2. Mock Cognitive Verifier (Success Case)
        with patch("core.improvement.cognitive_verifier.cognitive_verifier.verify_patch", new_callable=AsyncMock) as mock_verify:
            mock_verify.return_value = (True, 0.95, "Architect and Security reached consensus.")
            
            gov = AutonomousGovernor()
            
            # config değerlerini mock'la
            with patch("config.ENABLE_AUTONOMOUS_IMPROVEMENT", True), \
                 patch("config.IMPROVEMENT_AUTO_APPLY_THRESHOLD", 0.90):
                
                # apply_proposal'ı mock'la (Dosya yazılmasın)
                with patch.object(gov, "apply_proposal", new_callable=AsyncMock) as mock_apply:
                    await gov.run_cycle()
                    
                    # Doğrulamalar
                    mock_verify.assert_called_once()
                    mock_apply.assert_called_once()
                    assert len(gov.active_proposals) == 0 # Uygulandığı için listeden çıktı

@pytest.mark.asyncio
async def test_failure_learning_negative_synapse():
    """
    Reddedilen yamaların failure learning (Negatif Sinaps) mekanizmasını test eder.
    """
    with patch("core.improvement.observer.observer.scan_for_issues", new_callable=AsyncMock) as mock_scan, \
         patch("core.improvement.proposer.proposer.propose_fix", new_callable=AsyncMock) as mock_propose, \
         patch("core.improvement.cognitive_verifier.cognitive_verifier.verify_patch", new_callable=AsyncMock) as mock_verify:
        
        mock_scan.return_value = [{"reason": "security_vulnerability", "agent_id": "api/auth.py"}]
        mock_propose.return_value = "unsafe patch"
        mock_verify.return_value = (False, 0.2, "Security agent rejected: Unsafe path.")
        
        gov = AutonomousGovernor()
        await gov.run_cycle()
        
        # Negatif sinapsa eklenmiş olmalı
        assert "security_vulnerability" in gov.negative_synapses
        
        # İkinci kez tarandığında atlanmalı
        mock_propose.reset_mock()
        await gov.run_cycle()
        mock_propose.assert_not_called()

if __name__ == "__main__":
    asyncio.run(test_governor_cycle_with_cognitive_verifier())
    asyncio.run(test_failure_learning_negative_synapse())
    print("Cognitive Governance Tests: PASSED")
