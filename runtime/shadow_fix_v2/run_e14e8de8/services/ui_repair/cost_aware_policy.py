from typing import Dict, Any, Optional
from libs.db.models.ui_repair_models import UIRepairProjectProfile
from .budget_guard import BudgetGuard

class CostAwarePolicy:
    """Logic for selecting repair strategies based on financial and technical constraints."""
    
    @staticmethod
    async def get_repair_strategy(
        db: Any, # AsyncSession
        project_key: str, 
        failure_severity: str,
        is_critical_route: bool
    ) -> Dict[str, Any]:
        """
        Determine the optimal repair strategy considering budget and risk.
        """
        # 1. Check budget first
        is_allowed, reason, usage = await BudgetGuard.check_budget(db, project_key)
        
        # 2. Define basic strategies
        strategies = {
            "LIGHTWEIGHT": {
                "agent": "STAGEHAND",
                "mode": "DIAGNOSTIC_ONLY",
                "max_cost_usd": 0.5,
                "description": "Minimal cost diagnostic"
            },
            "STANDARD": {
                "agent": "OPENSWE",
                "mode": "FULL_REPAIR",
                "max_cost_usd": 5.0,
                "description": "Standard autonomous repair"
            },
            "ENTERPRISE": {
                "agent": "OPENSWE",
                "mode": "DEEP_REPAIR",
                "max_cost_usd": 15.0,
                "description": "High-fidelity recursive repair"
            }
        }
        
        # 3. Decision logic
        if not is_allowed:
            if is_critical_route:
                return {
                    "strategy": "LIGHTWEIGHT",
                    "reason": f"Budget blocked: {reason}. Downgrading to lightweight for critical route.",
                    "requires_approval": True,
                    **strategies["LIGHTWEIGHT"]
                }
            else:
                return {
                    "strategy": "NONE",
                    "reason": f"Budget blocked: {reason}. Skipping repair for non-critical route.",
                    "requires_approval": False,
                    "action": "NOTIFY_OPERATOR"
                }
                
        # High usage (>90%) -> prefer lightweight
        if usage > 90 and not is_critical_route:
            return {
                "strategy": "LIGHTWEIGHT",
                "reason": "High budget usage. Preferring lightweight strategy.",
                "requires_approval": True,
                **strategies["LIGHTWEIGHT"]
            }
            
        # Critical route or High severity -> Enterprise
        if is_critical_route or failure_severity == "CRITICAL":
            return {
                "strategy": "ENTERPRISE",
                "reason": "Critical route or severity requires highest fidelity repair.",
                "requires_approval": True,
                **strategies["ENTERPRISE"]
            }
            
        return {
            "strategy": "STANDARD",
            "reason": "Standard repair strategy for routine failures.",
            "requires_approval": True,
            **strategies["STANDARD"]
        }
