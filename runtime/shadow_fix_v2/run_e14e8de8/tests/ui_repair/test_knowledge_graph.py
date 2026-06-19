import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.ui_repair_models import (
    UIKnowledgeNode, UIKnowledgeEdge, KnowledgeNodeType, KnowledgeEdgeType,
    UIIncidentWarRoom, UIComplianceFinding, UICausalMemory, UIRiskPrediction,
    UICostAnomaly
)
from services.ui_repair.knowledge_graph_builder import KnowledgeGraphBuilder
from services.ui_repair.risk_prediction_engine import RiskPredictionEngine
from services.ui_repair.causal_memory_engine import CausalMemoryEngine

@pytest.mark.asyncio
async def test_knowledge_graph_rebuild(db_session: AsyncSession):
    # 1. Create source data
    war_room = UIIncidentWarRoom(
        id=uuid.uuid4(),
        incident_key="INC-001",
        title="Critical Database Latency",
        severity="P1_HIGH",
        status="OPEN",
        source_type="SECURITY_POSTURE_FINDING"
    )
    db_session.add(war_room)
    
    finding = UIComplianceFinding(
        id=uuid.uuid4(),
        description="Unencrypted S3 Bucket",
        severity="CRITICAL",
        standard="INTERNAL_SECURITY",
        finding_type="AWS_S3_001",
        project_key="DEFAULT",
        source_type="AUDIT",
        source_id="S3_001"
    )
    db_session.add(finding)
    
    await db_session.commit()
    
    # 2. Trigger rebuild
    builder = KnowledgeGraphBuilder(db_session)
    result = await builder.rebuild_graph()
    
    assert result["nodes"] >= 2
    
    # 3. Verify nodes
    from sqlalchemy import select
    nodes = (await db_session.execute(
        select(UIKnowledgeNode).order_by(UIKnowledgeNode.created_at)
    )).scalars().all()
    
    node_types = [n.node_type for n in nodes]
    assert KnowledgeNodeType.WAR_ROOM in node_types
    assert KnowledgeNodeType.SECURITY_FINDING in node_types

@pytest.mark.asyncio
async def test_risk_prediction_generation(db_session: AsyncSession):
    engine = RiskPredictionEngine(db_session)
    preds = await engine.generate_predictions()
    
    assert len(preds) > 0
    assert preds[0].probability > 0
    assert preds[0].status == "ACTIVE"

@pytest.mark.asyncio
async def test_causal_memory_recording(db_session: AsyncSession):
    engine = CausalMemoryEngine(db_session)
    
    memory_key = "DB_LATENCY_REPAIR"
    root_cause = "Missing index on users table"
    trigger = {"metric": "latency", "threshold": 500}
    action = {"type": "CREATE_INDEX", "sql": "CREATE INDEX idx_users_email ON users(email)"}
    outcome = {"result": "SUCCESS", "latency_after": 50}
    
    # Record first time
    memory = await engine.record_outcome(
        memory_key=memory_key,
        pattern_type="PERFORMANCE",
        root_cause=root_cause,
        trigger_conditions=trigger,
        action_taken=action,
        outcome=outcome,
        success_score=0.95
    )
    
    assert memory.recurrence_count == 1
    assert memory.success_score == 0.95
    
    # Record second time (learning)
    updated = await engine.record_outcome(
        memory_key=memory_key,
        pattern_type="PERFORMANCE",
        root_cause=root_cause,
        trigger_conditions=trigger,
        action_taken=action,
        outcome=outcome,
        success_score=0.85
    )
    
    assert updated.recurrence_count == 2
    # (0.95 + 0.85) / 2 = 0.9
    assert updated.success_score == pytest.approx(0.9)

@pytest.mark.asyncio
async def test_recommendation_retrieval(db_session: AsyncSession):
    engine = CausalMemoryEngine(db_session)
    
    # Seed a memory
    await engine.record_outcome(
        memory_key="AUTH_FIX_1",
        pattern_type="SECURITY",
        root_cause="Invalid JWT Secret",
        trigger_conditions={},
        action_taken={"fix": "Rotate secrets"},
        outcome={"status": "FIXED"},
        success_score=1.0
    )
    
    # Retrieve
    rec = await engine.get_best_remediation("JWT Secret")
    assert rec is not None
    assert rec["action"]["fix"] == "Rotate secrets"
    assert rec["expected_success"] == 1.0
