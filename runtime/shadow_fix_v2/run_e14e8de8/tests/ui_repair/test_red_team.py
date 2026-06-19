import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from libs.db.models.ui_repair_models import (
    UIRedTeamScenario, UIRedTeamRun, RedTeamRunStatus, RedTeamSafetyMode,
    RedTeamScenarioType, RedTeamTargetDomain
)
from services.ui_repair.autonomous_red_team_agent import AutonomousRedTeamAgent
from services.ui_repair.red_team_scenario_builder import RedTeamScenarioBuilder

@pytest.mark.asyncio
async def test_red_team_scenario_generation(db_session):
    """Verifies that the builder can create scenarios from attack paths and standards."""
    builder = RedTeamScenarioBuilder(db_session)
    
    # 1. Create standard scenarios
    scenarios = await builder.create_standard_scenarios()
    assert len(scenarios) > 0
    assert any(s.scenario_key == "RT-TENANT-X" for s in scenarios)
    
    # 2. Check persistence
    stmt = select(UIRedTeamScenario).where(UIRedTeamScenario.scenario_key == "RT-TENANT-X")
    res = await db_session.execute(stmt)
    saved = res.scalar_one()
    assert saved.target_domain == RedTeamTargetDomain.TENANT_ISOLATION

@pytest.mark.asyncio
async def test_red_team_operation_lifecycle(db_session):
    """Verifies a full Red Team operation: Generation -> Probe -> Drift -> Finding."""
    agent = AutonomousRedTeamAgent(db_session)
    builder = RedTeamScenarioBuilder(db_session)
    
    # 1. Setup scenario
    scenarios = await builder.create_standard_scenarios()
    scenario = scenarios[0]
    
    # 2. Trigger operation
    run = await agent.trigger_operation(scenario.id)
    assert run.status in [RedTeamRunStatus.PASSED, RedTeamRunStatus.FAILED]
    assert run.started_at is not None
    assert run.finished_at is not None
    
    # 3. Check for evidence
    from libs.db.models.core_models import SovereignEvidence
    stmt = select(SovereignEvidence).where(SovereignEvidence.evidence_type.like("RED_TEAM_%"))
    res = await db_session.execute(stmt)
    evidence = res.scalars().all()
    assert len(evidence) >= 2 # Started & Completed

@pytest.mark.asyncio
async def test_adversarial_drift_detection(db_session):
    """Verifies that drift is detected during operations."""
    from services.ui_repair.adversarial_drift_detector import AdversarialDriftDetector
    detector = AdversarialDriftDetector(db_session)
    
    run_id = uuid.uuid4()
    drifts = await detector.detect_drift(run_id, RedTeamTargetDomain.COGNITIVE_INTEGRITY)
    
    assert len(drifts) > 0
    assert drifts[0].drift_score > 0
    assert drifts[0].run_id == run_id

@pytest.mark.asyncio
async def test_red_team_report_generation(db_session):
    """Verifies executive report production."""
    from services.ui_repair.red_team_reporter import RedTeamReporter
    reporter = RedTeamReporter(db_session)
    
    start = datetime.now(timezone.utc)
    end = datetime.now(timezone.utc)
    
    report = await reporter.generate_report(start, end)
    assert report.report_name.startswith("Red Team Audit Report")
    assert report.executive_summary is not None
    assert "Critical Findings" in report.executive_summary
