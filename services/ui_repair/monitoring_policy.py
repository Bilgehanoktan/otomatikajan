from typing import List, Dict, Any, Optional
from uuid import UUID

class MonitoringPolicy:
    """
    Phase 6: Monitoring Policy.
    Determines which routes to monitor and when, based on system priority and recent failures.
    """

    @staticmethod
    def get_scoped_routes(config: Dict[str, Any], all_routes: List[str]) -> List[str]:
        """
        Determines the scope of routes for the current monitoring run.
        """
        config_scope = config.get("route_scope_json", [])
        if config_scope:
            return [r for r in config_scope if r in all_routes]
        
        # Default: Monitor all registered routes
        return all_routes

    @staticmethod
    def should_escalate_to_critical(failure_count: int, severity: str) -> bool:
        """
        Decides if a recurring failure should be escalated to CRITICAL.
        """
        if failure_count > 5 and severity == "HIGH":
            return True
        return False
