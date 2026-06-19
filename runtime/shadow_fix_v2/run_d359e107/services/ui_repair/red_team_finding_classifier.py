import uuid
from typing import List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.ui_repair_models import (
    UIRedTeamRun, UIRedTeamScenario, UIRedTeamFinding, 
    UIAdversarialProbe, UIAdversarialDriftEvent, RedTeamTargetDomain
)
from services.observability.logging import get_logger

_log = get_logger("red_team_classifier")

class RedTeamFindingClassifier:
    """Phase 24: Classifies Red Team failures and drift into actionable security findings."""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def classify_and_save(self, run: UIRedTeamRun, scenario: UIRedTeamScenario, probes: List[UIAdversarialProbe], drifts: List[UIAdversarialDriftEvent]):
        """Generates findings based on operation results."""
        findings = []
        
        # 1. Classify Probe Failures (False Allows)
        for probe in probes:
            if not probe.passed:
                finding = UIRedTeamFinding(
                    id=uuid.uuid4(),
                    run_id=run.id,
                    scenario_id=scenario.id,
                    finding_type="FALSE_ALLOW",
                    severity="CRITICAL" if scenario.risk_level == "HIGH" else "HIGH",
                    description=f"Guardrail Bypass: {probe.probe_type} was allowed when it should have been {probe.expected_decision}.",
                    affected_control=probe.probe_type,
                    affected_domain=probe.target_domain,
                    feasible=True
                )
                findings.append(finding)
                
        # 2. Classify Drift Events
        for drift in drifts:
            if drift.drift_score > 0.1: # Threshold for finding
                finding = UIRedTeamFinding(
                    id=uuid.uuid4(),
                    run_id=run.id,
                    scenario_id=scenario.id,
                    finding_type="ADVERSARIAL_DRIFT",
                    severity=drift.severity,
                    description=f"Security Drift Detected: {drift.description}",
                    affected_domain=drift.domain,
                    feasible=False
                )
                findings.append(finding)
                
        for f in findings:
            self.db.add(f)
            _log.info(f"Generated Red Team finding: {f.description}")
            
            # If critical, we would trigger an incident or remediation link here
            # In Phase 24, we just save them.
            
        await self.db.flush()
        return findings
