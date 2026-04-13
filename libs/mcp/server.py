import json
import logging
from typing import Callable, Dict, Any, List

logger = logging.getLogger("libs.mcp.server")

class MCPServer:
    """
    Minimal Model Context Protocol (MCP) server interface.
    This acts as the bridge for AGI components (like SovereignCortex)
    to dynamically discover and invoke tools in a standardized format.
    """

    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self._tools: Dict[str, dict] = {}
        self._handlers: Dict[str, Callable] = {}

    def register_tool(self, name: str, description: str, input_schema: dict, handler: Callable):
        """Register a tool exposing an MCP-compliant schema."""
        self._tools[name] = {
            "name": name,
            "description": description,
            "inputSchema": input_schema,
        }
        self._handlers[name] = handler
        logger.debug(f"[MCP] Registered tool: {name}")

    def list_tools(self) -> List[dict]:
        """Return exactly the format expected by an MCP client."""
        return list(self._tools.values())

    async def call_tool(self, name: str, arguments: dict) -> dict:
        """Invoke a tool with given JSON-compatible arguments."""
        if name not in self._handlers:
            raise ValueError(f"Tool '{name}' is not recognized by MCP server '{self.name}'.")

        logger.info(f"[MCP] Invoking tool '{name}'")
        try:
            handler = self._handlers[name]
            # Assumes async handers for now
            result = await handler(**arguments)
            return {
                "content": [{"type": "text", "text": json.dumps(result)}],
                "isError": False
            }
        except Exception as e:
            logger.error(f"[MCP] Tool '{name}' failed: {e}", exc_info=True)
            return {
                "content": [{"type": "text", "text": str(e)}],
                "isError": True
            }

