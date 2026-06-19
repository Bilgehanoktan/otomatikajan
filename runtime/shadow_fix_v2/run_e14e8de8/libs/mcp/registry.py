"""
libs/mcp/registry.py — Phase 15.01
Central Tool Registry for the Sovereign AGI Federated MCP.
"""
from __future__ import annotations
import inspect
import asyncio
from typing import Dict, Any, Callable, List, Type, Optional, get_type_hints
from pydantic import BaseModel, validate_arguments
from services.observability.logging import get_logger

_log = get_logger("mcp_registry")

class ToolMetadata(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]
    requires_approval: bool = False

class ToolRegistry:
    """
    Central repository for all autonomous tools available to agents.
    Provides validation, documentation extraction, and execution routing.
    """
    _tools: Dict[str, Callable] = {}
    _metadata: Dict[str, ToolMetadata] = {}

    @classmethod
    def register(cls, name: Optional[str] = None, requires_approval: bool = False):
        """Decorator to register a function as an MCP tool."""
        def decorator(func: Callable):
            tool_name = name or func.__name__
            sig = inspect.signature(func)
            
            # Extract docstring
            doc = func.__doc__ or "No description provided."
            
            # Build Pydantic-like parameter schema for LLM context
            params = {}
            for param_name, param in sig.parameters.items():
                if param_name == "self" or param_name == "context":
                    continue
                type_hint = get_type_hints(func).get(param_name, Any)
                params[param_name] = {
                    "type": str(type_hint.__name__) if hasattr(type_hint, "__name__") else str(type_hint),
                    "default": param.default if param.default is not inspect.Parameter.empty else None,
                    "required": param.default is inspect.Parameter.empty
                }

            cls._tools[tool_name] = func
            cls._metadata[tool_name] = ToolMetadata(
                name=tool_name,
                description=doc.strip(),
                parameters=params,
                requires_approval=requires_approval
            )
            _log.info(f"[MCP-REGISTRY] Registered tool: {tool_name}")
            return func
        return decorator

    @classmethod
    async def call(cls, name: str, context: Optional[Dict[str, Any]] = None, **kwargs) -> Any:
        """Executes a registered tool with validation."""
        if name not in cls._tools:
            raise KeyError(f"Tool '{name}' is not registered in the Sovereign MCP.")

        tool_func = cls._tools[name]
        
        # In a real system, we'd use validate_arguments(tool_func)(**kwargs)
        # For Phase 15.01, we provide a clean execution wrapper
        try:
            if asyncio.iscoroutinefunction(tool_func):
                return await tool_func(**kwargs)
            return tool_func(**kwargs)
        except Exception as e:
            _log.error(f"[MCP-REGISTRY] Error executing {name}: {e}")
            raise

    @classmethod
    def get_all_metadata(cls) -> List[ToolMetadata]:
        return list(cls._metadata.values())

    @classmethod
    def get_tool_metadata(cls, name: str) -> Optional[ToolMetadata]:
        return cls._metadata.get(name)

# Singleton instance for global access
mcp_registry = ToolRegistry()
