import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from core.agi.cognitive.sovereign_cortex import SovereignCortex
from core.agi.schemas import PlanProposal

@pytest.mark.asyncio
async def test_dialectic_planning_flow():
    """
    SovereignCortex'in bir hedef için diyalektik planlama (debate + consensus) yapıp 
    yürüttüğünü doğrular.
    """
    cortex = SovereignCortex()
    cortex.planner = MagicMock()
    cortex.planner.plan.return_value = [] # Subtasks
    
    # Mock Debate and Consensus
    with patch("core.agi.cognitive.debate_manager.debate_manager.argue", new_callable=AsyncMock) as mock_debate:
        mock_debate.return_value = [PlanProposal(agent_id="p1", content="plan 1")]
        
        with patch("core.agi.cognitive.consensus_manager.consensus_manager.resolve", new_callable=AsyncMock) as mock_resolve:
            mock_resolve.return_value = PlanProposal(
                agent_id="consensus", 
                content="final hybrid plan",
                metadata={"syntheris_logic": "merged"}
            )
            
            # 1. Yürütme
            task = await cortex._execute_dialectic_planning("t1", "Test Goal", "ctx", "desc")
            
            # 2. Doğrulama
            assert mock_debate.called
            assert mock_resolve.called
            assert task.description == "merged"
            print("Dialectic Planning Flow: SUCCESS")

@pytest.mark.asyncio
async def test_architectural_audit_rejection():
    """
    Kritik bir mimari değişikliğin (örneğin 'core refactor') AuditGate tarafından 
    reddedildiğinde görevin durdurulduğunu doğrular.
    """
    cortex = SovereignCortex()
    
    # Simulate Audit Rejection
    with patch("core.agi.security.audit_gate.audit_gate.verify_architecture_proposal", new_callable=AsyncMock) as mock_audit:
        mock_audit.return_value = False # REJECTED
        
        # Dialectic'i bypass et (Mock)
        with patch.object(cortex, "_execute_dialectic_planning", new_callable=AsyncMock) as mock_dialectic:
            from core.task_management import ProjectTask, TaskStatus
            mock_dialectic.return_value = ProjectTask(id="t2", title="CORE REFACTOR")
            
            # 1. Yürütme
            task = await cortex.coordinate_goal("CORE REFACTOR", "dangerous stuff")
            
            # 2. Doğrulama
            assert mock_audit.called
            assert task.status == TaskStatus.ERROR
            assert "DENETİM REDDİ" in task.report
            print("Architectural Audit Rejection: SUCCESS")

if __name__ == "__main__":
    asyncio.run(test_dialectic_planning_flow())
    asyncio.run(test_architectural_audit_rejection())
