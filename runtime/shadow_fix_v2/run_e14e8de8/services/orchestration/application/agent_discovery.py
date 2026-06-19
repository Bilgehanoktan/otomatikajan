"""
Application Layer Agent Discovery — Shim Module.
Re-exports agent registry functions for the application-layer sovereign_cortex.
"""
from agents.specialist_agents.agent_registry import (
    Agent,
    build_agents,
    discover_and_build_specialists,
)

__all__ = ["Agent", "build_agents", "discover_and_build_specialists"]
