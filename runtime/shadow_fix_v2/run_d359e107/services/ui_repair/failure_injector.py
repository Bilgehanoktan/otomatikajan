from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime
from services.observability.logging import get_logger

_log = get_logger("ui_failure_injector")

class FailureInjector:
    """
    Phase 8: Failure Injector.
    Manages controlled failure injections for UI Chaos Drills.
    """
    
    _active_injections: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def inject_failure(cls, scenario: Any) -> str:
        """
        Registers a failure injection.
        Returns an injection_id (token).
        """
        injection_id = str(uuid.uuid4())
        cls._active_injections[injection_id] = {
            "scenario_id": str(scenario.id),
            "failure_type": scenario.failure_type,
            "target_route": scenario.target_route,
            "target_api": scenario.target_api,
            "started_at": datetime.now(),
            "status": "ACTIVE"
        }
        _log.info(f"UI Chaos: Injected failure {scenario.failure_type} on {scenario.target_route} (ID: {injection_id})")
        return injection_id

    @classmethod
    def cleanup_injection(cls, injection_id: str):
        """Removes a specific injection."""
        if injection_id in cls._active_injections:
            del cls._active_injections[injection_id]
            _log.info(f"UI Chaos: Cleaned up injection {injection_id}")

    @classmethod
    def get_active_injections_for_route(cls, route: str) -> List[Dict[str, Any]]:
        """Returns active injections targeting a specific route."""
        return [inj for inj in cls._active_injections.values() if inj["target_route"] == route]

    @classmethod
    def get_active_injections_for_api(cls, api_path: str) -> List[Dict[str, Any]]:
        """Returns active injections targeting a specific API path."""
        return [inj for inj in cls._active_injections.values() if inj["target_api"] == api_path]
