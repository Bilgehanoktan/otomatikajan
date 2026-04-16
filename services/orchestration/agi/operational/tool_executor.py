import asyncio
import os
import subprocess
from datetime import datetime
from typing import Dict, Any, List, Optional
from services.observability.logging import get_logger
from services.integrations.web_search import get_web_search
from services.integrations.github_tool import get_github_tool
from services.orchestration.agi.operational.tool_grounder import get_grounded_tool_input
from services.governance.quality.output_schema import ToolCall
from libs.mcp.registry import mcp_registry
from libs.infra.ws_manager import ws_manager

_log = get_logger("tool_executor")

class ToolExecutor:
    """
    Standardized Tool Executor.
    Now integrated with MCP Registry and Workflow Observability.
    """
    def __init__(self):
        self.web_search = get_web_search()
        self.github = get_github_tool()
        self._register_default_tools()

    def _register_default_tools(self):
        """Registers built-in tools to the central registry if not already registered."""
        # Note: In a production system, these would be in separate integration files.
        # Here we register the core operational tools for Phase 15.01.
        
        @mcp_registry.register(name="read_file")
        async def read_file(path: str):
            """Core system tool to read file contents."""
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return {"content": f.read()[:20000]}
            raise FileNotFoundError(f"Path {path} does not exist.")

        @mcp_registry.register(name="run_shell_command", requires_approval=True)
        async def run_shell_command(command: str):
            """Execute a shell command with a 30s timeout."""
            process = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            return {
                "stdout": process.stdout,
                "stderr": process.stderr,
                "exit_code": process.returncode
            }

    async def execute_calls(self, task_id: str, agent_id: str, tool_calls: List[ToolCall], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Executes a batch of tool calls with deep logging and dashboard reporting.
        """
        results = []
        workflow_id = context.get("workflow_id", task_id)

        for call in tool_calls:
            _log.info(f"[TOOL-EXEC] Starting: {call.tool_name}")
            
            # 1. Grounding (Safety Check)
            grounded_input = await get_grounded_tool_input(task_id, call.tool_name, call.tool_input)
            if grounded_input in ["BLOCKED", "BLOCKED_PATH_ACCESS"]:
                results.append({"tool": call.tool_name, "status": "error", "error": f"Safety Blocked: {call.tool_name}"})
                continue

            # 2. Dashboard Event: Tool Started
            await ws_manager.broadcast({
                "type": "TOOL_STARTED",
                "workflow_id": workflow_id,
                "agent_id": agent_id,
                "tool_name": call.tool_name,
                "input": grounded_input,
                "timestamp": datetime.utcnow().isoformat()
            })

            try:
                # 3. Dynamic Registry Routing
                if call.tool_name in mcp_registry._tools:
                    res = await mcp_registry.call(call.tool_name, context=context, **grounded_input)
                
                # 4. Fallback for legacy integrations not yet fully migrated
                elif call.tool_name == "web_search":
                    query = grounded_input.get("query", "")
                    res = await self.web_search.search(query)
                elif call.tool_name == "github_pr":
                    res = await self.github.create_pull_request(**grounded_input)
                else:
                    raise NotImplementedError(f"Tool {call.tool_name} not found in registry or legacy fallback.")

                # 5. Dashboard Event: Tool Succeeded
                results.append({"tool": call.tool_name, "status": "success", "data": res})
                await ws_manager.broadcast({
                    "type": "TOOL_COMPLETED",
                    "workflow_id": workflow_id,
                    "tool_name": call.tool_name,
                    "status": "success",
                    "timestamp": datetime.utcnow().isoformat()
                })

            except Exception as e:
                _log.error(f"[TOOL-EXEC] Failure in {call.tool_name}: {e}")
                results.append({"tool": call.tool_name, "status": "error", "error": str(e)})
                await ws_manager.broadcast({
                    "type": "TOOL_FAILED",
                    "workflow_id": workflow_id,
                    "tool_name": call.tool_name,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })

        return results

tool_executor = ToolExecutor()
