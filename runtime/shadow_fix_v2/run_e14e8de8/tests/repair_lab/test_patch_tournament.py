import pytest
from unittest.mock import AsyncMock
from services.improve.patch_tournament import PatchTournament
from services.improve.benchmark_loader import BenchmarkCase
from datetime import datetime, timezone

@pytest.mark.asyncio
async def test_tournament_selects_winner():
    mock_orch = AsyncMock()
    mock_orch.complete.return_value = "FIX CONTENT"
    
    tournament = PatchTournament(model_orch=mock_orch)
    case = BenchmarkCase(
        id="re-001-replay-bug",
        incident_id="INC-TEST",
        module="test.module",
        title="Test Incident",
        description="Testing tournament",
        risk_class="medium",
        cost_class="low",
        target_behavior="stable",
        verification_profile={},
        input_context={"test": True, "logs": "some logs"},
        expected_signals={}
    )
    
    result = await tournament.run_tournament(case)
    assert result.winner_id is not None
    assert len(result.candidates) >= 1
    assert result.winning_rationale != ""
