from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid

class PilotStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class PilotMode(str, Enum):
    SHADOW_ONLY = "SHADOW_ONLY"
    ASSISTED_REPAIR = "ASSISTED_REPAIR"
    GOVERNED_REPAIR = "GOVERNED_REPAIR"
    LIMITED_PRODUCTION = "LIMITED_PRODUCTION"

class PilotRecommendation(str, Enum):
    GO = "GO"
    GO_WITH_WARNINGS = "GO_WITH_WARNINGS"
    EXTEND_PILOT = "EXTEND_PILOT"
    NO_GO = "NO_GO"

class PilotManager:
    """Manages the lifecycle of a controlled enterprise pilot rollout."""
    
    def __init__(self, rollout_id: str):
        self.rollout_id = rollout_id

    async def get_current_mode(self, db_session) -> PilotMode:
        # In a real impl, this would fetch from DB
        return PilotMode.GOVERNED_REPAIR

    async def is_action_allowed(self, action_type: str, mode: PilotMode) -> bool:
        """Determines if an action is allowed in the current pilot mode."""
        if action_type == "AUTO_APPLY":
            return False  # Always disabled in Pilot phase 11
        
        if mode == PilotMode.SHADOW_ONLY:
            allowed = ["MONITOR", "DIAGNOSE", "LOG"]
            return action_type in allowed
        
        if mode == PilotMode.ASSISTED_REPAIR:
            allowed = ["MONITOR", "DIAGNOSE", "LOG", "PROPOSE_PATCH"]
            return action_type in allowed
            
        if mode == PilotMode.GOVERNED_REPAIR:
            allowed = ["MONITOR", "DIAGNOSE", "LOG", "PROPOSE_PATCH", "REVIEW", "VERIFY", "GOVERNANCE_REQUEST"]
            return action_type in allowed
            
        return False
