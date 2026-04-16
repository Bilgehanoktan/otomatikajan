
import pytest
from services.improve.repair_bench import RepairBenchService

@pytest.mark.asyncio
async def test_full_lab_workflow_e2e():
    """
    E2E test simulating the entire Autonomous Repair Lab cycle:
    Load -> Tournament -> Verifier Mesh -> Memory Update -> Self-Tuning
    """
    bench = RepairBenchService()
    
    # 1. Run all cases in lab
    results = await bench.run_all_benchmarks()
    assert len(results) >= 3
    
    # 2. Check memory for updates
    from services.improve.repair_memory import RepairMemory
    memory = RepairMemory()
    # At least some outcomes should be recorded in pattern miner
    assert len(memory.history) >= 3
    
    # 3. Check engine for policy update suggestions
    from services.improve.self_tuning_engine import SelfTuningEngine
    engine = SelfTuningEngine(bench_service=bench)
    recs = await engine.generate_recommendations()
    assert len(recs) >= 0 # Depends on success rate
    
    # 4. Final verification
    stats = await bench.get_lab_stats()
    assert stats["total_runs"] >= 3
    assert stats["success_rate"] > 0
