
import pytest
from services.improve.verifier_mesh import VerifierMesh
from services.improve.models import RepairCandidate
from services.improve.benchmark_loader import BenchmarkCase

@pytest.mark.asyncio
async def test_verifier_mesh_aggregates_scores():
    mesh = VerifierMesh()
    candidate = RepairCandidate(
        type="patch",
        content="test fix",
        strategy="conservative"
    )
    case = BenchmarkCase(
        id="t-1", incident_id="i", module="m", title="t", description="d", 
        risk_class="low", cost_class="low", target_behavior="b", 
        verification_profile={}, input_context={}, expected_signals={}
    )
    
    evaluation = await mesh.verify_candidate(case, candidate)
    assert "build" in evaluation.scores.breakdown
    assert evaluation.scores.total_score <= 1.0
    assert evaluation.is_qualified is True
