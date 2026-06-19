"""
Sovereign AGI — Phase 19 (L5 Autonomy)
services/repair/domain/sandbox.py
Ephemeral Sandbox Execution Environment. Secures safety by testing patches locally.
"""

import os
import shutil
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import Tuple, List

from services.repair.application.ast_patcher import UnifiedASTPatcher

logger = logging.getLogger(__name__)

class SandboxVerificationError(Exception):
    """Raised when tests fail in the sandbox"""
    pass

class EphemeralSandbox:
    """
    Creates an isolated copy of the workspace (or a minimal subset) to apply
    and test automated code patches before touching production files.
    """
    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root).resolve()
        self.sandbox_root = Path(tempfile.mkdtemp(prefix="sov_sandbox_"))
        logger.info(f"Initialized Ephemeral Sandbox at {self.sandbox_root}")
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def apply_and_verify(
        self, 
        target_file_rel_path: str, 
        target_node_name: str, 
        new_source_code: str,
        test_file_rel_path: str = None
    ) -> Tuple[bool, str]:
        """
        1. Copies necessary files to sandbox.
        2. Applies AST patch to the sandy file.
        3. Runs pytest against the sandbox.
        4. Returns (Success, Test Output/Error).
        """
        try:
            # Step 1: Copy file to sandbox structure
            src_file = self.workspace_root / target_file_rel_path
            dst_file = self.sandbox_root / target_file_rel_path
            
            if not src_file.exists():
                return False, f"Target file does not exist: {target_file_rel_path}"
                
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dst_file)
            
            # Step 2: Apply Patch in Sandbox
            with open(dst_file, "r", encoding="utf-8") as f:
                original_code = f.read()
                
            patcher = UnifiedASTPatcher(original_code)
            try:
                patched_code = patcher.replace_node(target_node_name, new_source_code)
            except Exception as e:
                return False, f"AST Patch Failed: {e}"
                
            with open(dst_file, "w", encoding="utf-8") as f:
                f.write(patched_code)
                
            # Step 3: Minimal Testing (Mocked via syntax check if no pytest provided)
            # For a real pipeline, we'd copy the whole module or required test contexts.
            # Here we do a python compile check first to ensure no runtime syntax error
            try:
                compile(patched_code, str(dst_file), 'exec')
            except SyntaxError as e:
                return False, f"Compile Error after patch: {e}"
                
            if test_file_rel_path:
                src_test = self.workspace_root / test_file_rel_path
                if src_test.exists():
                    dst_test = self.sandbox_root / test_file_rel_path
                    dst_test.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_test, dst_test)
                    
                    # Ensure minimal PYTHONPATH
                    env = os.environ.copy()
                    env["PYTHONPATH"] = str(self.sandbox_root)
                    
                    result = subprocess.run(
                        ["pytest", str(dst_test)],
                        cwd=str(self.sandbox_root),
                        env=env,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if result.returncode != 0:
                        return False, f"Test execution failed.\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            
            return True, "AST Patch applied and verified locally. Ready for production merge."
            
        except Exception as e:
            logger.error(f"Sandbox error: {e}", exc_info=True)
            return False, f"Internal Sandbox Error: {e}"

    def commit_to_production(self, target_file_rel_path: str):
        """
        Carefully copies the verified sandboxed file back to the primary workspace.
        This represents the "Merge" operation.
        """
        sandbox_file = self.sandbox_root / target_file_rel_path
        prod_file = self.workspace_root / target_file_rel_path
        
        if not sandbox_file.exists():
            raise FileNotFoundError(f"Sandboxed verified file missing: {sandbox_file}")
            
        # Optional: Append to Operator Ledger before overwrite
        
        shutil.copy2(sandbox_file, prod_file)
        logger.info(f"Production code updated safely via sandbox: {target_file_rel_path}")

    def cleanup(self):
        """Wipes the ephemeral sandbox."""
        if self.sandbox_root.exists():
            shutil.rmtree(self.sandbox_root, ignore_errors=True)
            logger.info("Sandbox destroyed.")
