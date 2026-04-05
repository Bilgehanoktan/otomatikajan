
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

async def test_observer_logic():
    print("--- ImprovementObserver Mantık Testi (Mocked) ---")
    
    # 1. Mock dependencies
    mock_watchdog = AsyncMock()
    mock_watchdog.search_events.return_value = [
        {"agent_id": "backend_dev", "body": "Connection timeout"},
        {"agent_id": "backend_dev", "body": "Connection timeout"},
        {"agent_id": "backend_dev", "body": "Connection timeout"},
    ]
    
    mock_proj_repo = AsyncMock()
    mock_proj = MagicMock()
    mock_proj.id = "proj-123"
    mock_proj.title = "Failed System Task"
    mock_proj.assigned_agent = "qa_engineer"
    mock_proj.error_detail = "UnitTest failure in module X"
    mock_proj.description = "Fixing bugs"
    
    mock_proj_repo.list_recent.return_value = [mock_proj]

    # 2. Patch observer dependencies
    with patch("core.improvement.observer.watchdog", mock_watchdog), \
         patch("core.improvement.observer.ProjectRepository", mock_proj_repo), \
         patch("core.improvement.observer.AsyncSessionLocal") as mock_session:
        
        # Mock session context manager
        mock_session.return_value.__aenter__.return_value = AsyncMock()
        
        from packages.orchestration.improvement.observer import ImprovementObserver
        obs = ImprovementObserver()
        issues = await obs.scan_for_issues()
        
        print(f"Tespit edilen sorun sayısı: {len(issues)}")
        for issue in issues:
            print(f"- Tip: {issue['type']}, Ajan: {issue['agent_id']}, Sebep: {issue['reason']}")
            
        # Beklenen: 1 reliability (watchdog) + 1 agent_failure (DB)
        assert any(i["type"] == "reliability" for i in issues)
        assert any(i["type"] == "agent_failure" for i in issues)
        print("\n[SUCCESS] TEST BASARILI: Observer hem logları hem de DB'deki proje hatalarını yakalıyor.")

async def test_gate_logic():
    print("\n--- ImprovementGate Mantık Testi (Mocked) ---")
    
    mock_observer = AsyncMock()
    mock_observer.scan_for_issues.return_value = [
        {"type": "agent_failure", "agent_id": "sys", "reason": "Failure Reason X", "evidence": {}}
    ]
    
    # Proposer ve Verifier mockla
    from packages.orchestration.improvement.proposer import PatchProposer
    mock_proposer = AsyncMock(spec=PatchProposer)
    mock_proposer.propose_fix.return_value = "DIFF PATCH CONTENT"
    
    from packages.orchestration.improvement.verifier import PatchVerifier
    mock_verifier = AsyncMock(spec=PatchVerifier)
    mock_verifier.verify_patch.return_value = True

    from packages.orchestration.improvement.gate import ImprovementGate
    gate = ImprovementGate()
    
    with patch("core.improvement.gate.observer", mock_observer), \
         patch("core.improvement.gate.proposer", mock_proposer), \
         patch("core.improvement.gate.verifier", mock_verifier):
        
        await gate.run_cycle()
        proposals = await gate.get_proposals()
        print(f"Aktif Oneri Sayısı: {len(proposals)}")
        assert len(proposals) == 1
        assert proposals[0]["patch"] == "DIFF PATCH CONTENT"
        
        # Mükerrer testi
        await gate.run_cycle()
        proposals = await gate.get_proposals()
        print(f"Tekrar sonrası Oneri Sayısı (Mükerrer önleme): {len(proposals)}")
        assert len(proposals) == 1
        
        print("\n[SUCCESS] TEST BASARILI: Gate döngüsü düzgün çalışıyor ve mükerrer kayıtları engelliyor.")

async def run_all():
    await test_observer_logic()
    await test_gate_logic()

if __name__ == "__main__":
    asyncio.run(run_all())
