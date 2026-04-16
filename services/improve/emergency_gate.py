"""
Sovereign AGI — Phase 18
services/improve/emergency_gate.py
Hard Safety Gate for Autonomous Patching & Rollouts.
"""
from __future__ import annotations
from typing import Dict, Any, Optional
from services.governance.emergency_policy import EmergencyPolicyEngine, EmergencyState

class EmergencyGate:
    """Intercepts and validates rollouts against live emergency policies."""
    
    def __init__(self):
        self.policy_engine = EmergencyPolicyEngine()

    async def check_rollout_safety(self, project_id: str, current_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Final check before a patch is released to a pilot project.
        Returns: { 'safe': bool, 'reason': str, 'state': EmergencyState }
        """
        state = await self.policy_engine.evaluate_risk(current_metrics)
        
        # 1. Blocking Conditions
        if state == EmergencyState.SAFETY_FREEZE:
            return {
                "safe": False,
                "reason": "CRITICAL: System in SAFETY_FREEZE mode. All autonomous rollouts blocked.",
                "state": state
            }
            
        if state == EmergencyState.READ_ONLY:
             return {
                "safe": False,
                "reason": "WARNING: System in READ_ONLY mode. Infrastructure changes blocked.",
                "state": state
            }

        # 2. Risk Context Check (Simplified for Phase 18 prototype)
        health_score = current_metrics.get("health_score", 100)
        if health_score < 80:
             return {
                "safe": False,
                "reason": f"Risk High: System health ({health_score}) is below rollout safety threshold (80).",
                "state": EmergencyState.DEGRADED
            }

        return {
            "safe": True,
            "reason": "OK: Metrics within safety thresholds.",
            "state": EmergencyState.NORMAL
        }

    async def get_emergency_remedy(self, state: EmergencyState) -> str:
        """Returns the recommended fallback action string for a given state."""
        action_data = self.policy_engine.get_action_for_state(state)
        return action_data.get("action", "LOG_ONLY")
