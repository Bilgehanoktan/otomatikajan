from typing import Dict, Any
from .pilot_mode import PilotMode

class ShadowModePolicy:
    """Enforces automation limits and shadow mode constraints."""
    
    def __init__(self, mode: PilotMode):
        self.mode = mode

    def can_initiate_patch(self) -> bool:
        return self.mode in [PilotMode.ASSISTED_REPAIR, PilotMode.GOVERNED_REPAIR, PilotMode.LIMITED_PRODUCTION]

    def can_auto_request_governance(self) -> bool:
        return self.mode in [PilotMode.GOVERNED_REPAIR, PilotMode.LIMITED_PRODUCTION]

    def is_auto_apply_blocked(self) -> bool:
        return True # Strict constraint for Phase 11

    def get_summary(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "patch_allowed": self.can_initiate_patch(),
            "auto_governance": self.can_auto_request_governance(),
            "auto_apply": not self.is_auto_apply_blocked()
        }
