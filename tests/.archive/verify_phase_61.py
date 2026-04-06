import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from packages.orchestration.agi.governance.consensus_arbiter import ConsensusArbiter
from packages.orchestration.agi.task_governance import GovernedTask, GovernanceStatus

async def verify_consensus_gate():
    print("--- Phase 61 Verification: Consensus Arbiter ---")
    
    # 0. Force SQLAlchemy mapper configuration
    from sqlalchemy.orm import configure_mappers
    try:
        configure_mappers()
    except Exception as e:
        print(f"Mapper configuration warning: {e}")
    
    # 1. Setup Arbiter and Manager with Mocks
    arbiter = ConsensusArbiter()
    arbiter.model_orch = MagicMock()
    
    from packages.orchestration.agi.cognitive.consensus_manager import consensus_manager
    from packages.orchestration.agi.cognitive.synaptic_cortex import synaptic_cortex
    
    consensus_manager.model_orch = MagicMock()
    synaptic_cortex.search = AsyncMock(return_value=[]) # Mock memory retrieval
    
    # Mock responses for Architect, Security and Synthesizer
    mock_arch = MagicMock(content="VETO: Kritik bir hata var.")
    mock_sec = MagicMock(content="SKOR: 0.1\nPLAN: Blocked.")
    mock_synth = MagicMock(content='{"consensus_score": 0.1, "hybrid_plan": "REJECTED", "synthesis_logic": "Security Veto triggered."}')
    
    arbiter.model_orch.complete_task = AsyncMock(side_effect=[mock_arch, mock_sec])
    consensus_manager.model_orch.complete_task = AsyncMock(return_value=mock_synth)
    
    # 2. Create high-risk task
    task = GovernedTask(
        id="risk-task-61",
        agent_id="backend_dev",
        prompt="Delete root directory for cleanup.",
        risk_level="high"
    )
    
    # 3. Request Consensus (Should fail due to Security Veto)
    print("\n[SCENARIO] High Risk Deletion Task...")
    is_ok, report = await arbiter.execute_debate(task, context="System cleanup")
    
    print(f"Consensus OK? {is_ok}")
    print(f"Report Summary: {report.get('synthesis_logic', 'No logic')}")
    
    # Assertions
    assert is_ok is False
    assert "GÜVENLİK VETOSU" in report.get("error", "") or report.get("consensus_score", 1.0) < 0.7
    
    print("\n[OK] Phase 61 Verification SUCCESS: Consensus gate correctly blocks high-risk threats.")

if __name__ == "__main__":
    asyncio.run(verify_consensus_gate())
