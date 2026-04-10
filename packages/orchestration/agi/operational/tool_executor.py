import asyncio
from typing import Dict, Any, List, Optional
from packages.observability.logging import get_logger
from packages.integrations.web_search import get_web_search
from packages.integrations.github_tool import get_github_tool
from packages.orchestration.agi.operational.tool_grounder import get_grounded_tool_input
from packages.quality_assurance.output_schema import ToolCall

_log = get_logger("tool_executor")

class ToolExecutor:
    """
    Ajanlardan gelen otonom araç çağrılarını (Tool Calls) 
    yöneten ve icra eden merkezi köprü.
    """
    def __init__(self):
        self.web_search = get_web_search()
        self.github = get_github_tool()

    async def execute_calls(self, task_id: str, agent_id: str, tool_calls: List[ToolCall], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Ajanın talep ettiği tüm araçları sırayla icra eder."""
        results = []
        for call in tool_calls:
            _log.info(f"[TOOL-EXEC] {agent_id} araç çağrısı başlattı: {call.tool_name}")
            
            # 1. Grounding & Safety Check
            # Not: tool_grounder şu an context bekliyor, gelen inputu ground ediyoruz.
            grounded_input = await get_grounded_tool_input(task_id, agent_id, call.tool_input)
            
            if grounded_input == "BLOCKED":
                results.append({"tool": call.tool_name, "status": "error", "error": "Safety Block: Input disallowed by ToolGrounder"})
                continue

            # 2. Routing
            try:
                if call.tool_name == "web_search":
                    query = grounded_input.get("query", "")
                    res = await self.web_search.search(query)
                    results.append({"tool": "web_search", "status": "success", "data": res})

                elif call.tool_name == "github_pr":
                    res = await self.github.create_pull_request(
                        head=grounded_input.get("head"),
                        title=grounded_input.get("title"),
                        body=grounded_input.get("body"),
                        base=grounded_input.get("base", "main")
                    )
                    results.append({"tool": "github_pr", "status": "success" if res else "failed", "data": res})

                else:
                    _log.warning(f"[TOOL-EXEC] Tanımlanmamış araç: {call.tool_name}")
                    results.append({"tool": call.tool_name, "status": "error", "error": f"Tool {call.tool_name} not implemented in Phase 12.2"})

            except Exception as e:
                _log.error(f"[TOOL-EXEC] {call.tool_name} yürütme hatası: {e}")
                results.append({"tool": call.tool_name, "status": "error", "error": str(e)})

        return results

tool_executor = ToolExecutor()
