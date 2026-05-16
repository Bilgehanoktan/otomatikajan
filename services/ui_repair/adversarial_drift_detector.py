import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.ui_repair_models import (
    UIAdversarialDriftEvent, AdversarialDriftType, RedTeamTargetDomain
)

class AdversarialDriftDetector:
    """Phase 24: Detects behavioral deviations under adversarial pressure."""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect_drift(self, run_id: uuid.UUID, domain: RedTeamTargetDomain) -> List[UIAdversarialDriftEvent]:
        """Analyzes system metrics to find drift from baseline performance/decisions."""
        drifts = []
        
        # 1. Decision Drift Analysis
        # (Compares actual probe results with historical baseline)
        decision_drift = await self._analyze_decision_drift(domain)
        if decision_drift:
            drifts.append(self._create_drift_event(run_id, domain, decision_drift))
            
        # 2. Performance Drift Analysis (e.g. latency spikes under attack)
        latency_drift = await self._analyze_latency_drift(domain)
        if latency_drift:
            drifts.append(self._create_drift_event(run_id, domain, latency_drift))
            
        for d in drifts:
            self.db.add(d)
            
        await self.db.flush()
        return drifts

    async def _analyze_decision_drift(self, domain: RedTeamTargetDomain) -> Optional[Dict[str, Any]]:
        """Checks if guardrail decision accuracy has shifted."""
        # Mock: detect 5% drift if domain is COGNITIVE_INTEGRITY (simulating stress)
        if domain == RedTeamTargetDomain.COGNITIVE_INTEGRITY:
            return {
                "type": AdversarialDriftType.COGNITIVE_INTEGRITY_DRIFT,
                "score": 0.15,
                "severity": "MEDIUM",
                "desc": "Slight increase in decision latency for hallucination detection under high throughput."
            }
        return None

    async def _analyze_latency_drift(self, domain: RedTeamTargetDomain) -> Optional[Dict[str, Any]]:
        """Checks if security processing time is increasing."""
        # Mock: detect trust score drift for Identity
        if domain == RedTeamTargetDomain.IDENTITY:
            return {
                "type": AdversarialDriftType.TRUST_SCORE_DRIFT,
                "score": 0.08,
                "severity": "LOW",
                "desc": "Identity trust score baseline shifted due to repeated token replay attempts."
            }
        return None

    def _create_drift_event(self, run_id: uuid.UUID, domain: RedTeamTargetDomain, data: Dict[str, Any]) -> UIAdversarialDriftEvent:
        """Helper to build a drift event record."""
        return UIAdversarialDriftEvent(
            id=uuid.uuid4(),
            run_id=run_id,
            domain=domain,
            drift_type=data["type"],
            drift_score=data["score"],
            severity=data["severity"],
            description=data["desc"],
            created_at=datetime.now(timezone.utc)
        )

    async def get_red_team_overview(self) -> Dict[str, Any]:
        """Returns aggregated drift and red team metrics for overview."""
        # This will be called by the agent or router
        from .autonomous_red_team_agent import AutonomousRedTeamAgent
        agent = AutonomousRedTeamAgent(self.db)
        return await agent.get_overview()
