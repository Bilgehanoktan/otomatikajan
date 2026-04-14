import yaml
import os
from typing import Dict, Any
from services.observability.logging import get_logger

logger = get_logger("services.governance.rate_limit")

class RateLimitEngine:
    def __init__(self, config_path: str = "configs/cost_guardrails.yaml"):
        self.config_path = config_path

    def _load_config(self) -> Dict:
        if not os.path.exists(self.config_path):
            return {}
        with open(self.config_path, "r") as f:
            return yaml.safe_load(f)

    def check_rate_limit(self, key: str, current_count: int) -> Dict[str, Any]:
        """
        Check if a quota or rate limit is exceeded.
        """
        config = self._load_config()
        limits = config.get("rate_limits", {})
        limit = limits.get(key, 999999)
        
        if current_count >= limit:
            return {"allowed": False, "reason": f"Rate limit exceeded for {key}: {current_count} >= {limit}"}
        
        return {"allowed": True, "reason": "Within limits"}

rate_limit_engine = RateLimitEngine()
