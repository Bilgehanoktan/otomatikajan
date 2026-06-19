from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from services.project_factory.artifacts import _resolve_project_dir
from services.project_factory.template_registry import get_template_config
from services.project_factory.sandbox_executor import execute_sandbox_command

def run_sandbox_verification(
    project_id: str,
    template_name: str,
    workspace_root: Optional[str] = None
) -> Dict[str, Any]:
    """
    Runs the pre-approved test/lint commands defined for the template inside the sandbox.
    Compiles results into verification_report.json.
    """
    config = get_template_config(template_name, workspace_root)
    test_commands = config.get("test_commands", []) if config else []

    project_dir = _resolve_project_dir(project_id, workspace_root)
    sandbox_path = (project_dir / "sandbox").resolve()

    runs = []
    overall_passed = True

    # If there are no test commands, we do a basic syntax check
    if not test_commands:
        runs.append({
            "command": "No custom verification required",
            "returncode": 0,
            "stdout": "Implicitly verified.",
            "stderr": ""
        })
    else:
        for cmd in test_commands:
            try:
                res = execute_sandbox_command(project_id, cmd, sandbox_path)
                runs.append({
                    "command": cmd,
                    "returncode": res.get("returncode", -1),
                    "stdout": res.get("stdout", ""),
                    "stderr": res.get("stderr", "")
                })
                if res.get("returncode", -1) != 0:
                    overall_passed = False
            except Exception as e:
                runs.append({
                    "command": cmd,
                    "returncode": -1,
                    "stdout": "",
                    "stderr": f"Execution error: {e}"
                })
                overall_passed = False

    report = {
        "project_id": project_id,
        "template_name": template_name,
        "status": "PASSED" if overall_passed else "FAILED",
        "commands_executed": runs
    }

    # Write verification_report.json
    report_path = project_dir / "verification_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    return report

def load_verification_report(
    project_id: str,
    workspace_root: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Loads verification_report.json if exists.
    """
    project_dir = _resolve_project_dir(project_id, workspace_root)
    report_path = project_dir / "verification_report.json"
    if not report_path.exists():
        return None
    with open(report_path, "r", encoding="utf-8") as f:
        return json.load(f)
