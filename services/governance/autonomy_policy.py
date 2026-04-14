import yaml
import os
from typing import Dict, List, Any
from services.observability.logging import get_logger

logger = get_logger("services.governance.autonomy")

class AutonomyEngine:
    def __init__(self, config_path: str = "configs/autonomy_policy.yaml"):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        if not os.path.exists(self.config_path):
            logger.warning(f"Config {self.config_path} not found. Defaulting to L1.")
            return {"current_global_level": "L1", "levels": {"L1": {"auto_execute": false, "requires_approval": true}}}
        
        with open(self.config_path, "r") as f:
            return yaml.safe_load(f)

    def check_execution_permission(self, step_data: Dict) -> Dict[str, Any]:
        """
        Check if a step can be executed based on autonomy levels.
        Returns: {"allowed": bool, "requires_approval": bool, "reason": str}
        """
        level_key = self.config.get("current_global_level", "L1")
        policy = self.config.get("levels", {}).get(level_key, {})
        
        risk_score = step_data.get("risk_score", 0.0)
        tool_name = step_data.get("tool_name")
        
        # L4 Whitelist Check
        if level_key == "L4":
            whitelisted_tools = policy.get("whitelisted_tools", [])
            if tool_name in whitelisted_tools:
                return {"allowed": True, "requires_approval": False, "reason": "L4 Whitelisted Tool"}
        
        # Risk-based check for L2/L3
        max_risk = policy.get("max_risk_score", 0.0)
        auto_exec = policy.get("auto_execute", False)
        
        if auto_exec and risk_score <= max_risk:
            return {"allowed": True, "requires_approval": False, "reason": f"{level_key} Auto-execution (Risk {risk_score} <= {max_risk})"}
        
        if policy.get("requires_approval", True) or (policy.get("requires_approval_above_risk", False) and risk_score > max_risk):
            return {"allowed": False, "requires_approval": True, "reason": f"{level_key} Policy requires manual approval for risk {risk_score}"}

        return {"allowed": False, "requires_approval": True, "reason": "Default safety block"}

autonomy_engine = AutonomyEngine()
