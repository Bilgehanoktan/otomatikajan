"""
libs/mcp package — Phase 13.04
Reference implementation structure for the Model Context Protocol (MCP).
Allows standardizing exposing platform tools (e.g. read_file, run_workflow)
to any MCP-compliant LLM client.
"""
from libs.mcp.server import MCPServer

__all__ = ["MCPServer"]
