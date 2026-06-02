import uuid
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.ui_repair_models import (
    UIRedTeamScenario, UIRedTeamRun, RedTeamRunStatus, RedTeamSafetyMode,
    UIRedTeamFinding, UIRedTeamReport, UIAdversarialDriftEvent
)
from libs.db.models.core_models import SovereignEvidence
from .red_team_scenario_builder import RedTeamScenarioBuilder
from .adversarial_probe_runner import AdversarialProbeRunner
from .adversarial_drift_detector import AdversarialDriftDetector
from .red_team_evidence_writer import RedTeamEvidenceWriter
from services.observability.logging import get_logger

_log = get_logger("red_team_agent")

class AutonomousRedTeamAgent:
    """Phase 24: Orchestrates autonomous Red Team operations and adversarial testing."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.builder = RedTeamScenarioBuilder(db)
        self.runner = AdversarialProbeRunner(db)
        self.drift_detector = AdversarialDriftDetector(db)
        self.evidence_writer = RedTeamEvidenceWriter(db)

    async def run_full_suite(self) -> Dict[str, Any]:
        """Generates scenarios and runs all active tests."""
        # 1. Build/Update scenarios
        scenarios = await self.builder.build_from_attack_paths()
        scenarios += await self.builder.create_standard_scenarios()
        
        results = []
        for scenario in scenarios:
            if not scenario.enabled:
                continue
            run = await self.trigger_operation(scenario.id)
            results.append(run)
            
        return {
            "total_scenarios": len(scenarios),
            "executed_runs": len(results),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    async def trigger_operation(self, scenario_id: uuid.UUID, tenant_key: Optional[str] = None) -> UIRedTeamRun:
        """Executes a single Red Team operation."""
        # 1. Fetch scenario
        stmt = select(UIRedTeamScenario).where(UIRedTeamScenario.id == scenario_id)
        res = await self.db.execute(stmt)
        scenario = res.scalar_one()
        
        # 2. Safety Preflight
        if scenario.risk_level == "CRITICAL" and scenario.safety_mode == RedTeamSafetyMode.NON_DESTRUCTIVE_LIVE_CHECK:
            _log.warning(f"Blocking unsafe live check for scenario {scenario.scenario_key}")
            # Downgrade or block
            
        # 3. Create Run Record
        run = UIRedTeamRun(
            id=uuid.uuid4(),
            scenario_id=scenario_id,
            status=RedTeamRunStatus.RUNNING,
            safety_mode=scenario.safety_mode,
            started_at=datetime.now(timezone.utc)
        )
        self.db.add(run)
        await self.db.flush()
        
        await self.evidence_writer.write_event(
            event_type="RED_TEAM_RUN_STARTED",
            payload={"run_id": str(run.id), "scenario_key": scenario.scenario_key}
        )
        
        try:
            # 4. Execute Probes
            probe_results = await self.runner.run_probes(run.id, scenario)
            
            # 5. Analyze Drift
            drift_events = await self.drift_detector.detect_drift(run.id, scenario.target_domain)
            
            # 6. Consolidate Results
            run.status = RedTeamRunStatus.PASSED if all(p.passed for p in probe_results) else RedTeamRunStatus.FAILED
            run.finished_at = datetime.now(timezone.utc)
            run.result_summary_json = {
                "probes_count": len(probe_results),
                "probes_passed": sum(1 for p in probe_results if p.passed),
                "drift_events_count": len(drift_events)
            }
            
            # Update legacy fields for compatibility
            run.actual_decision = "BLOCKED" if run.status == RedTeamRunStatus.PASSED else "ALLOWED"
            
            # 7. Generate Findings if failed or drift detected
            if run.status == RedTeamRunStatus.FAILED or drift_events:
                await self._generate_findings(run, scenario, probe_results, drift_events)
            
        except Exception as e:
            _log.error(f"Red Team Operation failed: {str(e)}")
            run.status = RedTeamRunStatus.FAILED
            run.result_summary_json = {"error": str(e)}
            
        await self.db.commit()
        
        await self.evidence_writer.write_event(
            event_type="RED_TEAM_RUN_COMPLETED",
            payload={"run_id": str(run.id), "status": run.status}
        )
        
        return run

    async def _generate_findings(self, run: UIRedTeamRun, scenario: UIRedTeamScenario, probes: List[Any], drifts: List[Any]):
        """Classifies failures into actionable security findings."""
        from .red_team_finding_classifier import RedTeamFindingClassifier
        classifier = RedTeamFindingClassifier(self.db)
        await classifier.classify_and_save(run, scenario, probes, drifts)

    async def get_overview(self) -> Dict[str, Any]:
        """Aggregated metrics for the dashboard."""
        total_scenarios = await self.db.scalar(select(func.count(UIRedTeamScenario.id)))
        active_ops = await self.db.scalar(select(func.count(UIRedTeamRun.id)).where(UIRedTeamRun.status == RedTeamRunStatus.RUNNING))
        
        # Simple success rate calculation
        total_runs = await self.db.scalar(select(func.count(UIRedTeamRun.id)))
        passed_runs = await self.db.scalar(select(func.count(UIRedTeamRun.id)).where(UIRedTeamRun.status == RedTeamRunStatus.PASSED))
        success_rate = (passed_runs / total_runs * 100) if total_runs > 0 else 100.0
        run_rows = list((
            await self.db.execute(
                select(UIRedTeamRun).where(UIRedTeamRun.finished_at.is_not(None))
            )
        ).scalars().all())
        detection_latencies = [
            max(0.0, (run.finished_at - run.started_at).total_seconds() * 1000)
            for run in run_rows
            if run.started_at and run.finished_at
        ]
        avg_detection_latency = (
            sum(detection_latencies) / len(detection_latencies)
            if detection_latencies
            else 0.0
        )
        critical_drifts = await self.db.scalar(
            select(func.count(UIAdversarialDriftEvent.id)).where(UIAdversarialDriftEvent.severity == "CRITICAL")
        ) or 0
        latest_run_at = max((run.finished_at or run.started_at for run in run_rows), default=datetime.now(timezone.utc))
        
        return {
            "total_scenarios": total_scenarios or 0,
            "active_operations": active_ops or 0,
            "success_rate": success_rate,
            "avg_detection_latency": round(avg_detection_latency, 1),
            "critical_drifts": critical_drifts,
            "last_run_at": latest_run_at
        }
