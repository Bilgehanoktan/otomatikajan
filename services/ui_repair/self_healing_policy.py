from typing import Dict, Any, Tuple
from services.observability.logging import get_logger

_log = get_logger("ui_self_healing_policy")

class SelfHealingPolicy:
    """
    Phase 6: Self-Healing Policy Engine.
    Decides if the system should automatically trigger a repair for a detected failure.
    """

    @staticmethod
    def evaluate_auto_repair(
        config: Dict[str, Any], 
        case_data: Dict[str, Any], 
        stats: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Evaluates if auto-repair should be triggered.
        Returns (should_trigger, reason).
        """
        if not config.get("auto_repair_enabled", False):
            return False, "Auto-repair is disabled in configuration."

        risk_level = case_data.get("severity", "MEDIUM")
        threshold = config.get("auto_repair_risk_threshold", "LOW")
        
        # Risk levels: LOW < MEDIUM < HIGH < CRITICAL
        risk_map = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
        
        if risk_map.get(risk_level, 0) > risk_map.get(threshold, 0):
            return False, f"Case risk ({risk_level}) exceeds auto-repair threshold ({threshold})."

        # Check rate limits
        if stats.get("repairs_last_hour", 0) >= config.get("max_repairs_per_hour", 1):
            return False, "Hourly auto-repair limit reached."
            
        if stats.get("repairs_last_day", 0) >= config.get("max_repairs_per_day", 5):
            return False, "Daily auto-repair limit reached."

        return True, "Policy compliant. Initiating autonomous repair."
