import pytest
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.ui_repair_models import (
    UIAutoPatchExecution, UIPatchCandidate, UIPatchNegotiationSession,
    PatchNegotiationStatus, UIAutoPatchTrace
)
from services.ui_repair.autopatch_v2_orchestrator import AutoPatchV2Orchestrator
from services.ui_repair.autopatch_trace_collector import AutoPatchTraceCollector

@pytest.mark.asyncio
async def test_patch_negotiation_full_cycle(db_session: AsyncSession):
    # Setup
    execution = UIAutoPatchExecution(
        war_room_id=uuid.uuid4(),
        status="PATCH_PLANNING",
        source_type="WAR_ROOM_ACTION",
        execution_key=f"exec_{str(uuid.uuid4())[:8]}"
    )
    db_session.add(execution)
    await db_session.commit()
    await db_session.refresh(execution)
    
    candidate = UIPatchCandidate(
        execution_id=execution.id,
        strategy="REPLACE",
        candidate_key=f"cand_{str(uuid.uuid4())[:8]}",
        summary="Test patch",
        risk_level="LOW",
        verifier_score=0.9
    )
    db_session.add(candidate)
    await db_session.commit()
    await db_session.refresh(candidate)
    
    # Run negotiation via orchestrator
    orchestrator = AutoPatchV2Orchestrator(db_session)
    session = await orchestrator.negotiator.start_session(execution.id, ["AgentA", "AgentB"])
    
    assert session.status == PatchNegotiationStatus.RUNNING
    assert session.candidate_count == 1
    
    # Add debate turns
    turn = await orchestrator.negotiator.add_debate_turn(
        session.id, "AgentA", "CRITIQUE", "Looks good", candidate_id=candidate.id
    )
    assert turn.agent_name == "AgentA"
    
    # Finalize
    decision = await orchestrator.negotiator.finalize_session(
        session.id, "SELECTED_FOR_GOVERNANCE", selected_candidate_id=candidate.id, rationale="Best choice"
    )
    
    await db_session.refresh(session)
    assert session.status == PatchNegotiationStatus.CONSENSUS_REACHED
    assert session.selected_candidate_id == candidate.id
    assert decision.decision == "SELECTED_FOR_GOVERNANCE"

@pytest.mark.asyncio
async def test_trace_collection(db_session: AsyncSession):
    execution_id = uuid.uuid4()
    collector = AutoPatchTraceCollector(db_session)
    
    trace = await collector.start_trace(execution_id, "test_step", agent_name="test_agent")
    assert trace.status == "RUNNING"
    
    await collector.finish_trace(trace.id, "SUCCESS", cost_usd=0.01, token_input=100, token_output=50)
    
    await db_session.refresh(trace)
    assert trace.status == "SUCCESS"
    assert trace.cost_usd == 0.01
    assert trace.duration_ms >= 0
    assert trace.evidence_hash is not None
