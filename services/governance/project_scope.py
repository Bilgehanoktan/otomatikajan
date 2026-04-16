"""
Project Scope & Isolation Service
────────────────────────────────
Enforces boundary protection between projects (tenants).
Handles project-specific policies, secrets, and cost limits.
"""

from typing import Dict, Any, Optional
import os
import yaml
from uuid import UUID
from libs.config import DATA_DIR
import logging

logger = logging.getLogger(__name__)

class ProjectScope:
    def __init__(self, project_id: UUID, is_pilot: bool = False):
        self.project_id = project_id
        self.is_pilot = is_pilot
        self.config_path = os.path.join(DATA_DIR, "configs", "project_policies", f"{project_id}.yaml")
        self.default_config_path = os.path.join("configs", "project_policies", "default.yaml")
        self.policy = self._load_policy()
        
        # Apply Pilot Overrides
        if self.is_pilot:
            self._apply_pilot_overrides()

    def _load_policy(self) -> Dict[str, Any]:
        """Loads project-specific policy or falls back to default."""
        policy = {}
        # Load default first
        if os.path.exists(self.default_config_path):
            with open(self.default_config_path, "r") as f:
                policy = yaml.safe_load(f) or {}

        # Override with project-specific if exists
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                project_overrides = yaml.safe_load(f) or {}
                policy.update(project_overrides)
        
        return policy

    def _apply_pilot_overrides(self):
        """Hardens governance for pilot projects (Phase 15)."""
        logger.info(f"🛡️ PilotGuard active for project {self.project_id}")
        # Pilot projects are forced to Level 1 Autonomy (Human-in-the-loop)
        self.policy["max_autonomy_level"] = 1
        # Pilot projects have a default strict budget if not specified
        if "budget_limit" not in self.policy or self.policy["budget_limit"] <= 0:
            self.policy["budget_limit"] = 50.0 # $50 limit for pilots
        # Mandatory audit trail
        self.policy["audit_required"] = True

    def get_secret(self, key: str) -> Optional[str]:
        """Retrieves a project-scoped secret."""
        secrets = self.policy.get("secrets", {})
        return secrets.get(key)

    def check_cost_limit(self, current_cost: float) -> bool:
        """Checks if the project has exceeded its specific budget."""
        limit = self.policy.get("budget_limit", 0.0)
        if limit <= 0.0:
            return True # Unlimited
        return current_cost < limit

    def get_autonomy_level(self) -> int:
        """Returns allowed autonomy level (1-4)."""
        return self.policy.get("max_autonomy_level", 1)

class PilotGuard:
    """Utility class for pilot project verification."""
    @staticmethod
    def enforce_pilot_policy(scope: ProjectScope):
        if scope.is_pilot:
            # Additional runtime enforcement logic can go here
            if scope.get_autonomy_level() > 1:
                logger.warning(f"⚠️ Pilot project {scope.project_id} attempted high autonomy. Forcing Level 1.")
                # This is already enforced in __init__, but we can add safety checks here

class ProjectIsolationMiddleware:
    """
    Middleware pattern to ensure project context is enforced.
    (Conceptual - to be integrated with workflow_api)
    """
    @staticmethod
    def validate_access(user_id: UUID, project_id: UUID, db_session):
        # Implementation would verify ownership in DB
        pass
