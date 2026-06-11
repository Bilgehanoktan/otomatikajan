import ast
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Tuple, Optional

from services.repair.external_agents.agent_policy_engine import AgentPolicyEngine
from services.repair.external_agents.agent_sandbox_executor import _ignore_for_sandbox
from services.repair.evidence_pack import REPO_ROOT

class AgentOutputVerifier:
    @classmethod
    def verify_syntax(cls, file_path: Path) -> Tuple[bool, str]:
        """Parses a Python file using AST to ensure it has valid syntax."""
        try:
            if not file_path.exists():
                return False, f"File does not exist: {file_path}"
            
            # Read file content
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            
            # Parse AST
            ast.parse(content)
            return True, "Syntax is valid."
        except SyntaxError as e:
            return False, f"Syntax Error: {e.msg} at line {e.lineno}, col {e.offset}"
        except Exception as e:
            return False, f"Syntax verification failed: {e}"

    @classmethod
    def extract_patch_targets(cls, patch_path: Path) -> List[str]:
        """Extracts target files affected by a unified diff patch."""
        targets = []
        try:
            if not patch_path.exists():
                return []
            
            with open(patch_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if line.startswith("+++ b/"):
                        # Get target path, strip leading b/ and any trailing tab/metadata
                        target = line[6:].strip().split('\t')[0]
                        targets.append(target)
        except Exception:
            pass
        return targets

    @classmethod
    def verify_patch_structure(
        cls, 
        patch_path: Path, 
        allowed_dirs: List[str], 
        blocked_dirs: List[str]
    ) -> Tuple[bool, str]:
        """Validates that a patch does not touch restricted paths or escape target directories."""
        targets = cls.extract_patch_targets(patch_path)
        if not targets:
            return False, "Patch does not modify any files or is not in valid unified diff format."

        # Verify each target path using policy engine path validator
        # We temporarily resolve relative to REPO_ROOT for validation
        paths_ok, err_msg = AgentPolicyEngine.validate_paths(
            target_paths=targets,
            workspace_root=REPO_ROOT,
            allowed_dirs=allowed_dirs,
            blocked_dirs=blocked_dirs
        )
        return paths_ok, err_msg

    @classmethod
    async def dry_run_patch(
        cls, 
        patch_path: Path, 
        test_path: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Dry-runs applying a patch inside a temporary clone workspace and runs unit tests."""
        # 1. Initialize temporary workspace
        temp_root = Path(tempfile.mkdtemp(prefix="agent-promotion-dry-run-"))
        temp_workspace = temp_root / "workspace"
        
        try:
            # Copy codebase (optimized ignore list)
            shutil.copytree(REPO_ROOT, temp_workspace, ignore=_ignore_for_sandbox)
            
            # Initialize git so git apply runs cleanly
            subprocess.run(["git", "init"], cwd=temp_workspace, capture_output=True, shell=False)
            subprocess.run(["git", "config", "user.name", "DeerFlow Bot"], cwd=temp_workspace, capture_output=True, shell=False)
            subprocess.run(["git", "config", "user.email", "bot@deerflow.local"], cwd=temp_workspace, capture_output=True, shell=False)
            subprocess.run(["git", "add", "."], cwd=temp_workspace, capture_output=True, shell=False)
            subprocess.run(["git", "commit", "-m", "initial"], cwd=temp_workspace, capture_output=True, shell=False)

            # 2. Check patch application
            check_res = subprocess.run(
                ["git", "apply", "--check", str(patch_path)],
                cwd=temp_workspace,
                capture_output=True,
                text=True,
                shell=False
            )
            
            if check_res.returncode != 0:
                err = check_res.stderr or check_res.stdout or "Unknown git apply error."
                return False, f"Patch dry-run application check failed:\n{err}"
            
            # 3. Apply patch
            apply_res = subprocess.run(
                ["git", "apply", str(patch_path)],
                cwd=temp_workspace,
                capture_output=True,
                text=True,
                shell=False
            )
            if apply_res.returncode != 0:
                err = apply_res.stderr or apply_res.stdout or "Unknown git apply error."
                return False, f"Patch application failed:\n{err}"

            # 4. If test_path is provided, run unit tests inside dry-run workspace
            if test_path:
                import sys
                test_res = subprocess.run(
                    [sys.executable, "-m", "pytest", test_path, "-v"],
                    cwd=temp_workspace,
                    capture_output=True,
                    text=True,
                    shell=False
                )
                if test_res.returncode != 0:
                    err = test_res.stderr or test_res.stdout
                    return False, f"VerifierMesh test run failed inside dry-run workspace:\n{err}"
            
            return True, "Patch applied cleanly and all tests passed."
            
        except Exception as e:
            return False, f"Unexpected error during patch dry-run: {e}"
        finally:
            # Cleanup
            shutil.rmtree(temp_root, ignore_errors=True)
