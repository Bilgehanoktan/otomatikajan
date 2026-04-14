"""
Integration Capability Registry
──────────────────────────────
Tracks what each integration / connector is allowed to do.
Supports allowlisting tools and enforcing execution standards.
"""

from typing import List, Dict, Any, Optional
import yaml
import os

class CapabilityRegistry:
    def __init__(self, config_path: str = "configs/integration_policies.yaml"):
        self.config_path = config_path
        self.registry = self._load()

    def _load(self) -> Dict[str, Any]:
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                return yaml.safe_load(f) or {}
        return {}

    def get_connector_policy(self, connector_id: str) -> Dict[str, Any]:
        """Returns the specific policy for a connector."""
        # Generic fallback if not defined
        default_policy = {
            "allowed_tools": ["*"],
            "timeout_s": 30,
            "max_retries": 3,
            "risk_level": "controlled"
        }
        return self.registry.get("connectors", {}).get(connector_id, default_policy)

    def is_tool_allowed(self, connector_id: str, tool_name: str) -> bool:
        policy = self.get_connector_policy(connector_id)
        allowed = policy.get("allowed_tools", ["*"])
        if "*" in allowed:
            return True
        return tool_name in allowed

class IntegrationGuard:
    """Enforces integration governance at runtime."""
    def __init__(self, registry: CapabilityRegistry):
        self.registry = registry

    def validate_call(self, connector_id: str, tool_name: str):
        if not self.registry.is_tool_allowed(connector_id, tool_name):
            raise PermissionError(f"Tool '{tool_name}' is not allowed for connector '{connector_id}'")
        
        policy = self.registry.get_connector_policy(connector_id)
        # Here we could record governance check in audit log
        return policy
