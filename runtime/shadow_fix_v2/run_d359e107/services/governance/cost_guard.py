import yaml
import os
from typing import Dict, Any
from services.observability.logging import get_logger

logger = get_logger("services.governance.cost")

class CostGuard:
    def __init__(self, config_path: str = "configs/cost_guardrails.yaml"):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        if not os.path.exists(self.config_path):
            logger.warning(f"Config {self.config_path} not found. Defaulting to safe values.")
            return {"max_cost_per_workflow": 5.0}
        
        with open(self.config_path, "r") as f:
            return yaml.safe_load(f)

    def check_budget_limit(self, current_cost: float, project_limit: float = 0.0) -> Dict[str, Any]:
        """
        Validates if current cost is within workflow and global limits.
        """
        # Load latest config for dynamic limit changes
        config = self._load_config()
        
        hard_limit = config.get("max_cost_per_workflow", 25.0)
        # Use project specific limit if it exists and is lower than hard limit
        effective_limit = min(project_limit, hard_limit) if project_limit > 0 else hard_limit
        
        if current_cost >= effective_limit:
            return {
                "blocked": True,
                "reason": f"Budget breached: current ${current_cost:.4f} >= limit ${effective_limit:.4f}",
                "limit": effective_limit
            }
            
        return {"blocked": False, "reason": "Within budget"}

cost_guard = CostGuard()
