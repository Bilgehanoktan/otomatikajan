import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from libs.db.models.ui_repair_models import UIPolicyEvaluation, UIPolicyRule
from services.ui_repair.policy_as_code_engine import PolicyAsCodeEngine
from services.ui_repair.schemas import PolicyDecision

logger = logging.getLogger(__name__)

class PolicySimulator:
    """
    Simulates new policy rules against historical evaluation data.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def simulate_rule(self, proposed_rule_json: Dict[str, Any], project_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Runs a simulation of a proposed rule against the last 100 historical evaluations.
        """
        # 1. Fetch historical data
        stmt = select(UIPolicyEvaluation).order_by(UIPolicyEvaluation.evaluated_at.desc()).limit(100)
        if project_key:
             stmt = stmt.where(UIPolicyEvaluation.project_key == project_key)
        
        res = await self.db.execute(stmt)
        history = res.scalars().all()

        if not history:
            return {"status": "NO_HISTORY", "message": "No historical evaluation data found for simulation."}

        # 2. Setup temporary rule
        temp_rule = UIPolicyRule(
            policy_key="SIM_TEMP",
            scope="GLOBAL",
            rule_definition_json=proposed_rule_json,
            enabled=True
        )
        
        # 3. Initialize engine with just this rule
        engine = PolicyAsCodeEngine([temp_rule])

        # 4. Simulate
        allowed = 0
        denied = 0
        impact_summary = []

        for entry in history:
            context = entry.input_context_json
            action = entry.action_type
            
            result = engine.evaluate(action, context)
            
            if result["decision"] in [PolicyDecision.DENY, PolicyDecision.BLOCKED_BY_BUDGET]:
                denied += 1
                impact_summary.append({
                    "action": action,
                    "target": entry.target_id,
                    "previous_decision": entry.decision,
                    "new_decision": result["decision"],
                    "reason": result["reason"]
                })
            else:
                allowed += 1

        return {
            "status": "COMPLETED",
            "evaluations_scanned": len(history),
            "allow_count": allowed,
            "deny_count": denied,
            "impact_percent": (denied / len(history)) * 100 if history else 0,
            "impact_samples": impact_summary[:5] # Top 5 samples
        }
