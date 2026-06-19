import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.ui_repair_models import (
    UIRedTeamFinding, UIRedTeamScenario, UIGuardrailTuningProposal, 
    GuardrailTuningStatus, UIDefensivePattern, UIPolicyRegressionRun,
    UIGuardrailCanaryRun
)
from services.ui_repair.guardrail_optimization_engine import GuardrailOptimizationEngine
from services.ui_repair.tuning_proposal_service import TuningProposalService

@pytest.mark.asyncio
async def test_defense_optimization_lifecycle(db_session: AsyncSession):
    """Verifies the full defensive optimization lifecycle."""
    engine = GuardrailOptimizationEngine(db_session)
    service = TuningProposalService(db_session)
    
    # 1. Setup: Create a Red Team Finding
    finding = UIRedTeamFinding(
        id=uuid.uuid4(),
        run_id=uuid.uuid4(),
        scenario_id=uuid.uuid4(),
        finding_type="TENANT_BYPASS",
        severity="CRITICAL",
        description="Observed potential cross-tenant leak in tool execution.",
        affected_domain="TENANT_ISOLATION",
        affected_control="TenantIsolationGuard",
        feasible=True
    )
    db_session.add(finding)
    await db_session.commit()
    
    # 2. Step: Run Optimization Cycle (Synthesis + Tuning)
    proposals = await engine.run_optimization_cycle()
    assert len(proposals) > 0
    proposal_id = proposals[0].id
    
    # 3. Verify Pattern Synthesis
    patterns = await service.get_patterns()
    assert len(patterns) > 0
    assert any(p.source_finding_id == finding.id for p in patterns)
    
    # 4. Step: Promote to Regression
    proposal = await engine.promote_proposal(proposal_id)
    assert proposal.status == GuardrailTuningStatus.REGRESSION_PASSED
    
    # 5. Verify Regression Run
    reg_runs = await service.get_regression_runs(proposal_id)
    assert len(reg_runs) == 1
    assert reg_runs[0].status == "PASSED"
    
    # 6. Step: Promote to Canary
    proposal = await engine.promote_proposal(proposal_id)
    assert proposal.status == GuardrailTuningStatus.CANARY_RUNNING
    
    # 7. Step: Complete Canary (Directly calling runner for test)
    canary_run = (await service.get_canary_runs(proposal_id))[0]
    await engine.canary.complete_canary(canary_run.id, force_success=True)
    
    # Refresh and check
    await db_session.refresh(proposal)
    assert proposal.status == GuardrailTuningStatus.CANARY_PASSED
    
    # 8. Step: Promote to Governance
    proposal = await engine.promote_proposal(proposal_id)
    assert proposal.status == GuardrailTuningStatus.GOVERNANCE_REQUESTED
    
    # 9. Step: Manual Approval
    await service.approve_proposal(proposal_id)
    assert proposal.status == GuardrailTuningStatus.APPROVED
    
    # 10. Step: Final Application
    await engine.apply_proposal(proposal_id)
    assert proposal.status == GuardrailTuningStatus.APPLIED
    
    print("\n[PASS] Defense Optimization Lifecycle verified.")

@pytest.mark.asyncio
async def test_safety_policy_enforcement(db_session: AsyncSession):
    """Ensures proposals that weaken policy are rejected."""
    engine = GuardrailOptimizationEngine(db_session)
    
    # Create a proposal that lowers threshold
    proposal = UIGuardrailTuningProposal(
        id=uuid.uuid4(),
        proposal_key="TP-WEAK-01",
        source_type="MANUAL",
        affected_guardrail="TestGuard",
        affected_policy_key="test.policy",
        current_config_json={"threshold": 0.8},
        proposed_config_json={"threshold": 0.4}, # Weakening!
        reason="Testing safety policy",
        risk_level="MEDIUM",
        status=GuardrailTuningStatus.DRAFT
    )
    db_session.add(proposal)
    await db_session.commit()
    
    # Promote
    result = await engine.promote_proposal(proposal.id)
    assert result.status == GuardrailTuningStatus.REJECTED
    assert "SAFETY_BLOCK" in result.reason
    
    print("[PASS] Safety Policy Enforcement verified.")
