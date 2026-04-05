import os
import shutil
import tempfile
import subprocess
from typing import Dict, Any
from .models import PatchProposal, VerificationResult

class PatchVerifier:
    """Verifies a patch proposal by running tests in a isolated temp directory."""

    def __init__(self, project_root: str):
        self.project_root = project_root

    async def verify(self, proposal: PatchProposal) -> VerificationResult:
        """
        1. Create a temp directory and copy the project.
        2. Apply the patch diff.
        3. Run pytest in the temp directory.
        4. Capture results and cleanup.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Copy project (excluding .git and __pycache__)
            shutil.copytree(
                self.project_root, 
                temp_dir, 
                ignore=shutil.ignore_patterns(".git", "__pycache__", "venv", ".pytest_cache"),
                dirs_exist_ok=True
            )
            
            # Apply patch
            patch_file = os.path.join(temp_dir, "proposed_fix.patch")
            with open(patch_file, "w", encoding="utf-8") as f:
                f.write(proposal.diff)
            
            try:
                # Use 'patch' command (typical on Unix/WSL) or 'git apply'
                # On Windows, we might need a specific tool or use python to apply
                # For now, let's try 'patch' or a Python-based simple applier
                apply_cmd = ["patch", "-p1", "-i", "proposed_fix.patch"]
                subprocess.run(apply_cmd, cwd=temp_dir, check=True, capture_output=True)
                
                # Run tests
                test_cmd = ["python", "-m", "pytest", "tests/test_faz4.py", "--tb=short"]
                test_proc = subprocess.run(test_cmd, cwd=temp_dir, capture_output=True, text=True)
                
                success = test_proc.returncode == 0
                details = test_proc.stdout + "\n" + test_proc.stderr
                
                return VerificationResult(
                    proposal_id=proposal.id,
                    tests_passed=success,
                    test_details=details,
                    benchmark_before={"avg_latency": 0.0}, # Placeholder for actual metrics
                    benchmark_after={"avg_latency": 0.0},
                    security_ok=True # Should include static analysis check later
                )
                
            except subprocess.CalledProcessError as e:
                return VerificationResult(
                    proposal_id=proposal.id,
                    tests_passed=False,
                    test_details=f"Failed to apply patch or run tests: {e.stderr.decode() if e.stderr else str(e)}",
                    benchmark_before={},
                    benchmark_after={},
                    security_ok=False
                )
            except Exception as e:
                return VerificationResult(
                    proposal_id=proposal.id,
                    tests_passed=False,
                    test_details=f"Unexpected error: {str(e)}",
                    benchmark_before={},
                    benchmark_after={},
                    security_ok=False
                )
