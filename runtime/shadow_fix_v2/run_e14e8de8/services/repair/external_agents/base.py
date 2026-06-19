from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from services.repair.external_agents.models import ExternalAgentContext, ExternalAgentResult


class ExternalAgentAdapter(ABC):
    @property
    @abstractmethod
    def agent_key(self) -> str:
        """The identifier of the external agent (matches catalog key)."""
        pass

    @property
    @abstractmethod
    def supported_modes(self) -> list[str]:
        """Modes supported by this adapter."""
        pass

    @abstractmethod
    def run(self, context: ExternalAgentContext) -> ExternalAgentResult:
        """Execute the external agent within the provided context."""
        pass

    @abstractmethod
    def validate_context(self, context: ExternalAgentContext) -> None:
        """Validate if the context meets the safety/governance rules of the adapter."""
        pass

    @abstractmethod
    def build_artifacts(self, result: ExternalAgentResult) -> dict[str, Any]:
        """Format and persist output artifacts in the directory structure."""
        pass
