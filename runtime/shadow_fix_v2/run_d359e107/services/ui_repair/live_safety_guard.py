from typing import Dict, Any
from .pilot_mode import PilotMode

class LiveSafetyGuard:
    """Enforces strict safety rules during live pilot rollout."""
    
    @staticmethod
    def validate_action(action: str, context: Dict[str, Any]) -> bool:
        """Returns True if the action is safe to proceed, False otherwise."""
        
        # 1. Auto-apply is strictly disabled in Phase 11
        if action == "AUTO_APPLY":
            return False
            
        # 2. Apply requires governance approval
        if action == "APPLY":
            if not context.get("governance_approved"):
                return False
            if not context.get("rollback_snapshot_exists"):
                return False
            if not context.get("evidence_chain_ready"):
                return False
                
        # 3. Crisis Mode checks
        if context.get("crisis_mode_active"):
            # Only allow monitoring/diagnosing in crisis mode
            allowed = ["MONITOR", "DIAGNOSE"]
            return action in allowed
            
        # 4. Lockdown checks
        if context.get("full_lockdown"):
            return action == "MONITOR"
            
        # 5. Critical file changes require manual approval
        if action == "GOVERNANCE_REQUEST" and context.get("high_risk_files"):
            if not context.get("operator_pre_approved"):
                return False
                
        return True
