from __future__ import annotations

import logging
from typing import Dict

from services.repair.external_agents.base import ExternalAgentAdapter
from services.repair.external_repo_integrations import load_external_agent_catalog

logger = logging.getLogger(__name__)


class ExternalAgentRegistry:
    _registry: Dict[str, ExternalAgentAdapter] = {}

    @classmethod
    def register(cls, adapter: ExternalAgentAdapter) -> None:
        """Register a new external agent adapter, validating against external_agent_catalog.yaml."""
        catalog = load_external_agent_catalog()
        agents = catalog.get("external_agents", {})
        if adapter.agent_key not in agents:
            raise PermissionError(
                f"Agent '{adapter.agent_key}' is not registered in the external agent catalog."
            )
        cls._registry[adapter.agent_key] = adapter
        logger.info("Registered external agent adapter: %s", adapter.agent_key)

    @classmethod
    def get_adapter(cls, agent_key: str) -> ExternalAgentAdapter:
        """Retrieve the adapter for a given agent_key. Raises PermissionError if not found/unknown."""
        if not cls._registry and agent_key == "swe_agent":
            from services.repair.external_agents.mock_adapter import MockExternalAgentAdapter
            cls.register(MockExternalAgentAdapter())

        if agent_key not in cls._registry:
            raise PermissionError(
                f"External agent adapter '{agent_key}' is unknown or not registered in the runtime registry."
            )
        return cls._registry[agent_key]

    @classmethod
    def clear(cls) -> None:
        cls._registry.clear()
