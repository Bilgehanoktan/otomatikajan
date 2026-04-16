
import pytest
from services.improve.repair_memory import RepairMemory
from services.improve.models import RepairMemoryEntry, RepairCandidate
from services.improve.patch_ranker import PatchRanker
from services.improve.benchmark_loader import BenchmarkCase

@pytest.mark.asyncio
async def test_memory_penalty_application():
    memory = RepairMemory()
    ranker = PatchRanker()
    
    case = BenchmarkCase(
        id="re-001", incident_id="I-1", module="libs.workflow",
        title="T", description="D", risk_class="med", cost_class="low",
        target_behavior="B", verification_profile={}, input_context={}, expected_signals={}
    )
    
    # Reset memory for test
    memory.history = []
    
    # Simulate a history of failures for 'radical' in 'libs.workflow'
    for _ in range(5):
        memory.record_outcome(RepairMemoryEntry(
            case_id="re-001", incident_type="drift", subsystem="libs.workflow",
            patch_strategy="radical", outcome="failure", score=0.1
        ))
    
    # Check if pattern says penalize
    pattern = memory.get_pattern_for_strategy("radical", "libs.workflow")
    assert pattern.recommendation == "penalize"
    
    # Check if ranker applies it
    candidate = RepairCandidate(type="patch", content="fix", strategy="radical")
    evaluation = await ranker.evaluate_candidate(case, candidate)
    
    # Base score without penalty would be something like 0.7*weights... 
    # But since all verifiers mock 0.7-1.0, a 0.5 penalty should clearly drop it.
    assert evaluation.scores.total_score < 0.6
