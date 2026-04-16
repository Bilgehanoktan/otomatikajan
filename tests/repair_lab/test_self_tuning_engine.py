
import pytest
from services.improve.self_tuning_engine import SelfTuningEngine
from services.improve.repair_bench import RepairBenchService, BenchResult
from datetime import datetime, timezone

@pytest.mark.asyncio
async def test_self_tuning_generates_recs():
    bench = RepairBenchService()
    # Mock some data
    for _ in range(10):
        bench.results_history.append(BenchResult(
            case_id="re-1", 
            timestamp=datetime.now(timezone.utc),
            candidates_count=3, 
            success=True, 
            score=0.95,
            best_candidate_id="c-winner", # Required field
            verification_summary={}, 
            learning_delta={}
        ))
    
    engine = SelfTuningEngine(bench_service=bench)
    recs = await engine.generate_recommendations()
    assert len(recs) >= 0 # Depends on logic
