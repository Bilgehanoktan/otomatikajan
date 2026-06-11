import os
import sys
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from services.repair.external_agents.agent_policy_engine import AgentPolicyEngine
from services.repair.external_agents.agent_ledger_reporter import AgentLedgerReporter
from services.repair.external_agents.agent_capability_registry import AgentCapabilityRegistry
from services.repair.evidence_pack import REPO_ROOT

def _ignore_for_sandbox(_: str, names: List[str]) -> set[str]:
    return {
        name
        for name in names
        if name in {
            ".git",
            ".venv",
            "node_modules",
            ".next",
            "__pycache__",
            ".pytest_cache",
            "repair_outputs",
            ".legacy_archive",
            ".backup",
            ".codex",
            "brain",
            "scratch",
            "tmp",
            "workspace",
            ".playwright-browsers",
            ".nx",
            ".agents",
            ".agent",
            ".codex_skill_staging",
            "e",
            "uploads",
            "project_outputs",
            "reports",
            "benchmarks",
            "runtime",
            "docs",
            "repair_outputs",
            "coverage_html_report",
            "htmlcov",
        }
        or name.endswith(".pyc")
        or name.endswith(".db")
        or name.endswith(".db-shm")
        or name.endswith(".db-wal")
        or name.endswith(".rar")
        or name in {".coverage", "coverage.xml", "pytest_output.txt"}
    }

def _copy_path_into_sandbox(source: Path, destination_root: Path) -> None:
    if not source.exists():
        return

    relative = source.relative_to(REPO_ROOT)
    destination = destination_root / relative
    destination.parent.mkdir(parents=True, exist_ok=True)

    if source.is_dir():
        if destination.exists():
            return
        shutil.copytree(source, destination, ignore=_ignore_for_sandbox)
    else:
        shutil.copy2(source, destination)


def _prepare_sandbox_workspace(
    sandbox_workspace: Path,
    command_handler: str,
    target_paths: List[str],
) -> None:
    """Create a minimal sandbox copy instead of copying the whole repository."""
    sandbox_workspace.mkdir(parents=True, exist_ok=True)

    seed_paths = set(target_paths or [])
    if command_handler == "run_tests":
        seed_paths.update({"tests", "services", "libs", "apps", "pytest.ini"})
    elif command_handler == "inspect_repo":
        seed_paths.update(target_paths or [])
    elif command_handler in {"generate_patch", "browser_check"}:
        seed_paths.update({"pytest.ini"})

    for raw_path in sorted(seed_paths):
        if not raw_path:
            continue
        source = (REPO_ROOT / raw_path).resolve()
        try:
            source.relative_to(REPO_ROOT)
        except ValueError:
            continue
        _copy_path_into_sandbox(source, sandbox_workspace)

class PredefinedHandlers:
    @staticmethod
    def get_args(handler_name: str, arguments: Dict[str, Any]) -> List[str]:
        """Returns safe process arguments (shell=False) for allowlisted handlers."""
        if handler_name == "run_tests":
            # Target path must be verified by the policy engine
            test_path = arguments.get("test_path", "tests/ui_repair")
            return [sys.executable, "-m", "pytest", test_path, "-v"]
            
        elif handler_name == "inspect_repo":
            target_file = arguments.get("target_file", "services/ui_repair/service.py")
            # Runs a safe python snippet to print the file
            return [sys.executable, "-c", "import sys; print(open(sys.argv[1], encoding='utf-8').read())", target_file]
            
        elif handler_name == "generate_patch":
            # Simulates a safe patch generator: writes a mock diff to a file
            patch_content = arguments.get("patch_content", "diff --git a/file b/file\n--- a/file\n+++ b/file\n")
            output_patch_path = arguments.get("output_patch_path", "patch.diff")
            return [
                sys.executable, 
                "-c", 
                "import sys, os; f=open(sys.argv[1], 'w', encoding='utf-8'); f.write(sys.argv[2]); f.close(); print('Patch generated at', sys.argv[1])", 
                output_patch_path, 
                patch_content
            ]
            
        elif handler_name == "browser_check":
            url = arguments.get("url", "http://localhost:3000")
            # Safe python check
            return [
                sys.executable, 
                "-c", 
                "import sys; print('Smoke check request to url:', sys.argv[1])", 
                url
            ]
            
        raise ValueError(f"Unknown predefined handler: {handler_name}")

class AgentSandboxExecutor:
    @classmethod
    async def execute_run(
        cls,
        db: AsyncSession,
        run_id: str,
        agent_key: str,
        command_handler: str,
        arguments: Dict[str, Any],
        target_paths: List[str],
        cost: float,
        network_domains: Optional[List[str]] = None,
        created_by: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str]]:
        """Executes an external agent run inside a secure sandbox environment."""
        capability = await AgentCapabilityRegistry.get_agent_capability(db, agent_key)
        if not capability:
            err = f"Agent '{agent_key}' is not registered in the capability database."
            return False, err, None

        # 1. Initialize temporary workspace
        temp_root = Path(tempfile.mkdtemp(prefix="agent-sandbox-"))
        sandbox_workspace = temp_root / "workspace"
        
        # Populate a minimal sandbox copy. Copying the whole repository can pull
        # runtime DB files, cache folders and frontend build artifacts into each
        # agent run, which makes tests and safe executions unnecessarily slow.
        _prepare_sandbox_workspace(sandbox_workspace, command_handler, target_paths)

        # Create Ledger record
        run_record = await AgentLedgerReporter.create_run_record(
            db=db,
            run_id=run_id,
            agent_key=agent_key,
            input_parameters={"handler": command_handler, "arguments": arguments, "target_paths": target_paths},
            sandbox_mode=capability.sandbox_mode,
            network_policy=capability.network_policy,
            created_by=created_by,
            timeout_seconds=300
        )

        # 2. Policy engine validation (relative to canonical resolved sandbox path)
        is_valid, violation_msg = await AgentPolicyEngine.validate_execution(
            db=db,
            agent_key=agent_key,
            command_handler=command_handler,
            target_paths=target_paths,
            cost=cost,
            workspace_root=sandbox_workspace,
            network_domains=network_domains
        )

        if not is_valid:
            shutil.rmtree(temp_root, ignore_errors=True)
            await AgentLedgerReporter.complete_run_record(
                db=db,
                run_id=run_id,
                exit_code=1,
                stdout="",
                stderr=violation_msg,
                cost=cost,
                commands_executed=[],
                policy_violations=[violation_msg],
                status="BLOCKED"
            )
            return False, f"Policy violation: {violation_msg}", None

        # 3. Start run tracking
        await AgentLedgerReporter.start_run_record(db, run_id, str(sandbox_workspace))

        # 4. Resolve Handler Arguments
        try:
            cmd_args = PredefinedHandlers.get_args(command_handler, arguments)
        except Exception as e:
            shutil.rmtree(temp_root, ignore_errors=True)
            err_msg = f"Handler argument resolution failed: {e}"
            await AgentLedgerReporter.complete_run_record(
                db=db,
                run_id=run_id,
                exit_code=1,
                stdout="",
                stderr=err_msg,
                cost=cost,
                commands_executed=[],
                policy_violations=[err_msg],
                status="FAILED"
            )
            return False, err_msg, None

        # 5. Run process safely (shell=False, with timeout)
        stdout, stderr, exit_code = "", "", 1
        status = "COMPLETED"
        start_time = time.monotonic()
        try:
            # Enforce execution timeout limits
            timeout = 300
            res = subprocess.run(
                cmd_args,
                cwd=sandbox_workspace,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=False
            )
            stdout = res.stdout
            stderr = res.stderr
            exit_code = res.returncode
            if exit_code != 0:
                status = "FAILED"
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or ""
            stderr = f"Execution timed out after {timeout} seconds."
            exit_code = 124
            status = "FAILED"
        except Exception as exc:
            stderr = f"Sandbox execution error: {exc}"
            exit_code = 1
            status = "FAILED"

        duration = time.monotonic() - start_time

        # 6. Mode handling (read-only vs workspace-write)
        preserved_workspace_path = None
        if capability.sandbox_mode == "workspace-write":
            # For workspace-write, we preserve the temp workspace for admin / Human Gate review
            # but we NEVER mutate the main repo directly
            preserved_workspace_path = str(sandbox_workspace)
        else:
            # read-only -> discard all changes
            shutil.rmtree(temp_root, ignore_errors=True)

        # 7. Complete Ledger record
        await AgentLedgerReporter.complete_run_record(
            db=db,
            run_id=run_id,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            cost=cost,
            commands_executed=[" ".join(cmd_args)],
            policy_violations=[],
            status=status
        )

        return (exit_code == 0), stdout if exit_code == 0 else stderr, preserved_workspace_path
