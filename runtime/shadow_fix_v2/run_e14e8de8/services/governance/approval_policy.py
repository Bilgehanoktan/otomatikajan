import yaml
import os
from typing import Dict, Any, Optional
from services.observability.logging import get_logger

logger = get_logger("services.governance.approval")

class ApprovalEngine:
    def __init__(self, config_path: str = "configs/approval_matrix.yaml"):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        if not os.path.exists(self.config_path):
            logger.warning(f"Config {self.config_path} not found. Defaulting to manual only.")
            return {"matrix": []}
        
        with open(self.config_path, "r") as f:
            return yaml.safe_load(f)

    def determine_approval_requirement(self, action_type: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Determines the required approval level for an action based on the matrix.
        """
        config = self._load_config()
        matrix = config.get("matrix", [])
        
        # Default fallback
        decision = {"action": "MANUAL_ONLY", "risk": "unknown", "reason": "No matching policy"}
        
        for rule in matrix:
            if rule.get("criteria") in action_type:
                return {
                    "action": rule.get("action"),
                    "risk": rule.get("risk"),
                    "reason": f"Matched criteria: {rule.get('criteria')}"
                }
        
        return decision

approval_engine = ApprovalEngine()
