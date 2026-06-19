import logging
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from libs.db.models.ui_repair_models import (
    UIRedTeamOperation, UIAdversarialDriftRecord
)

logger = logging.getLogger(__name__)

class AdversarialDriftDetector:
    """Phase 24: Detects security behavior deviations during Red Team pressure."""
    
    def __init__(self, session: AsyncSession):
        self.session = session

    async def analyze_operation_drift(self, operation_id: uuid.UUID) -> List[UIAdversarialDriftRecord]:
        """
        Analyzes an operation to see if system behavior drifted from historical baselines.
        """
        stmt = select(UIRedTeamOperation).where(UIRedTeamOperation.id == operation_id)
        res = await self.session.execute(stmt)
        op = res.scalar_one_or_none()
        
        if not op:
            return []
            
        drifts = []
        
        # Scenario 1: Latency Drift
        if op.detection_latency_ms and op.detection_latency_ms > 1000:
            drift = UIAdversarialDriftRecord(
                operation_id=op.id,
                drift_type="LATENCY_SPIKE",
                severity="MEDIUM",
                baseline_value_json={"avg_latency_ms": 250},
                observed_value_json={"actual_latency_ms": op.detection_latency_ms},
                impact_score=0.45,
                metadata_json={"reason": "Excessive detection delay during exfiltration simulation"}
            )
            drifts.append(drift)
            
        # Scenario 2: Guardrail Failure Drift (Hypothetical)
        if op.outcome == "SUCCESS": # Red Team succeeded (bypassed)
            drift = UIAdversarialDriftRecord(
                operation_id=op.id,
                drift_type="GUARDRAIL_FAILURE",
                severity="CRITICAL",
                baseline_value_json={"expected_outcome": "BLOCKED"},
                observed_value_json={"actual_outcome": "SUCCESS"},
                impact_score=0.95,
                metadata_json={"reason": "Security bypass detected in production-like scenario"}
            )
            drifts.append(drift)
            
        for d in drifts:
            self.session.add(d)
            
        await self.session.commit()
        return drifts

    async def get_red_team_overview(self) -> Dict[str, Any]:
        """
        Aggregates metrics for the Red Team dashboard.
        """
        # In a real impl, these would be aggregated queries
        return {
            "total_scenarios": 12,
            "active_operations": 2,
            "success_rate": 0.08, # Red Team success rate (lower is better for defense)
            "avg_detection_latency": 450.5,
            "critical_drifts": 1,
            "last_run_at": datetime.now(timezone.utc).isoformat()
        }
