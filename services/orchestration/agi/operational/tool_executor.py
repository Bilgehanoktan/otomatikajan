import asyncio
import os
import subprocess
from typing import Dict, Any, List, Optional
from services.observability.logging import get_logger
from services.integrations.web_search import get_web_search
from services.integrations.github_tool import get_github_tool
from services.orchestration.agi.operational.tool_grounder import get_grounded_tool_input
from services.governance.quality.output_schema import ToolCall

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
            grounded_input = await get_grounded_tool_input(task_id, call.tool_name, call.tool_input)
            
            if grounded_input == "BLOCKED_PATH_ACCESS" or grounded_input == "BLOCKED":
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

                elif call.tool_name == "apply_patch":
                    # Faz 12.3: Otonom Dosya Modifikasyonu
                    from services.orchestration.agi.cognitive.sovereign_cortex import sovereign_cortex
                    target_path = grounded_input.get("target_path") or grounded_input.get("file_path")
                    instruction = grounded_input.get("instruction")
                    
                    if not target_path or not instruction:
                        results.append({"tool": "apply_patch", "status": "error", "error": "Missing target_path or instruction"})
                        continue
                        
                    res_msg = await sovereign_cortex.self_updater.modify_system_file(target_path, instruction)
                    results.append({"tool": "apply_patch", "status": "success" if "Başarılı" in res_msg else "failed", "message": res_msg})

                elif call.tool_name == "code_repair":
                    # Faz 12.3: Otonom Hata Onarımı
                    from services.repair.application.heal_engine import heal_engine
                    from services.orchestration.agi.cognitive.sovereign_cortex import sovereign_cortex
                    target_path = grounded_input.get("target_path") or grounded_input.get("file_path")
                    error_msg = grounded_input.get("error_msg", "Unknown error")
                    
                    # Heal engine üzerinden otonom onarımı dene
                    # Not: Burada tam bir SubTask nesnesi gerekebilir, şimdilik basitleştirilmiş mock
                    res_msg = await sovereign_cortex.self_updater.modify_system_file(
                        target_path, 
                        f"Bu dosyadaki şu hatayı gider: {error_msg}"
                    )
                    results.append({"tool": "code_repair", "status": "success" if "Başarılı" in res_msg else "failed", "message": res_msg})

                elif call.tool_name in ["read_file", "view_file"]:
                    path = grounded_input.get("path") or grounded_input.get("file_path")
                    if os.path.exists(path):
                        with open(path, "r", encoding="utf-8") as f:
                            content = f.read()
                        results.append({"tool": call.tool_name, "status": "success", "content": content[:10000]}) # Limit output
                    else:
                        results.append({"tool": call.tool_name, "status": "error", "error": f"File not found: {path}"})

                elif call.tool_name == "list_dir":
                    path = grounded_input.get("path") or "."
                    if os.path.isdir(path):
                        items = os.listdir(path)
                        results.append({"tool": "list_dir", "status": "success", "items": items})
                    else:
                        results.append({"tool": "list_dir", "status": "error", "error": f"Directory not found: {path}"})

                elif call.tool_name == "git_create_fix_branch":
                    issue_id = grounded_input.get("issue_id", "evolve")
                    branch_name = f"AutoRepair/fix-{issue_id}"
                    # Git komutunu çalıştır
                    try:
                        subprocess.run(["git", "checkout", "-b", branch_name], check=True, capture_output=True)
                        results.append({"tool": "git_create_fix_branch", "status": "success", "branch": branch_name})
                    except Exception as git_err:
                        results.append({"tool": "git_create_fix_branch", "status": "error", "error": str(git_err)})

                elif call.tool_name == "run_shell_command":
                    command = grounded_input.get("command")
                    if not command:
                        results.append({"tool": "run_shell_command", "status": "error", "error": "No command provided"})
                        continue
                    
                    # Sandbox safety is handled by ToolGrounder, but we add a timeout here
                    try:
                        # Run command with 30s timeout
                        process = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
                        results.append({
                            "tool": "run_shell_command", 
                            "status": "success" if process.returncode == 0 else "failed",
                            "stdout": process.stdout,
                            "stderr": process.stderr,
                            "code": process.returncode
                        })
                    except subprocess.TimeoutExpired:
                        results.append({"tool": "run_shell_command", "status": "error", "error": "Command timeout (30s)"})
                    except Exception as cmd_err:
                        results.append({"tool": "run_shell_command", "status": "error", "error": str(cmd_err)})

                else:
                    _log.warning(f"[TOOL-EXEC] Tanımlanmamış araç: {call.tool_name}")
                    results.append({"tool": call.tool_name, "status": "error", "error": f"Tool {call.tool_name} not implemented in Phase 12.2"})

            except Exception as e:
                _log.error(f"[TOOL-EXEC] {call.tool_name} yürütme hatası: {e}")
                results.append({"tool": call.tool_name, "status": "error", "error": str(e)})

        return results


tool_executor = ToolExecutor()
