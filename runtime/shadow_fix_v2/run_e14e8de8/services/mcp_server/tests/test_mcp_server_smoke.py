"""
Smoke tests for services/mcp_server module.
"""
import pytest


def test_mcp_tools_importable():
    """The MCP tools module should be importable without errors."""
    from libs.mcp import tools
    assert hasattr(tools, 'WorkflowReplayInput')
    assert hasattr(tools, 'WorkflowDiagnosisInput')


def test_mcp_registry_importable():
    """The MCP registry module should be importable without errors."""
    from libs.mcp.registry import mcp_registry
    assert mcp_registry is not None
