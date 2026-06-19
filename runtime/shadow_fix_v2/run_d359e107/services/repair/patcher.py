import os
import re
import asyncio
import ast
from typing import List, Tuple
try:
    from observability.logging import get_logger
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("services.repair.patcher")
else:
    logger = get_logger("services.repair.patcher")

class AutonomousPatcher:
    """
    Phase 12: Autonomous Patching System.
    Scans for common anti-patterns (like unawaited coroutines) and fixes them.
    """
    def __init__(self, project_root: str):
        self.project_root = project_root
        # Common async functions that are often forgotten to be awaited
        self.async_functions = ["is_db_available", "verify_db_connection", "init_db", "close_db"]

    def scan_and_patch(self):
        """Main loop: scan, detect, and patch."""
        logger.info("👔 Autonomous Patcher: Starting system-wide scan...")
        patches_applied = []

        for root, dirs, files in os.walk(self.project_root):
            if any(d in root for d in [".git", "__pycache__", "venv", "node_modules"]):
                continue
                
            for file in files:
                if file.endswith(".py"):
                    path = os.path.join(root, file)
                    if "patcher.py" in path or "tmp_" in file:
                        continue # Skip self and temp test files (unless explicitly targeted)
                    
                    found, fixed_content = self._analyze_file(path)
                    if found:
                        logger.info(f"👔 Autonomous Patcher: Found unawaited calls in {file}. Patching...")
                        with open(path, "w", encoding="utf-8") as f:
                            f.write(fixed_content)
                        patches_applied.append(path)

        return patches_applied

    def patch_specific_file(self, path: str):
        """Targeted patch for a specific file (e.g. for testing)."""
        found, fixed_content = self._analyze_file(path)
        if found:
            with open(path, "w", encoding="utf-8") as f:
                f.write(fixed_content)
            return True
        return False

    def _analyze_file(self, path: str) -> Tuple[bool, str]:
        """Uses regex and simple string matching to find unawaited calls to known async functions."""
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content
        found = False

        for func in self.async_functions:
            # Pattern: matches func() when NOT preceded by 'await ' or 'def '
            # We look for matches like 'if is_db_available():' or 'res = is_db_available()'
            # Negative lookbehind for 'await ' or 'def '
            # Note: We use a more careful lookbehind or just check line-by-line
            
            # Simple line-by-line check instead of global re.sub for safety
            new_lines = []
            for line in content.split("\n"):
                if f"def {func}" in line:
                    new_lines.append(line)
                    continue
                
                # Check for unawaited call
                pattern = rf"(?<!await\s){re.escape(func)}\(\)"
                if re.search(pattern, line):
                    line = re.sub(pattern, f"await {func}()", line)
                    found = True
                new_lines.append(line)
            
            content = "\n".join(new_lines)

        return found, content

if __name__ == "__main__":
    # Self-test or standalone run
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    patcher = AutonomousPatcher(root)
    
    # Test on the temp file
    test_file = os.path.join(root, "tmp_test_unawaited.py")
    if os.path.exists(test_file):
        print(f"Testing patcher on {test_file}...")
        if patcher.patch_specific_file(test_file):
            print("DONE: Successfully patched tmp_test_unawaited.py")
        else:
            print("INFO: tmp_test_unawaited.py was already clean.")

    # Full system scan
    print("\nStarting SYSTEM-WIDE scan...")
    patched_files = patcher.scan_and_patch()
    if patched_files:
        print(f"DONE: Patched {len(patched_files)} files:")
        for f in patched_files:
            print(f"  - {f}")
    else:
        print("DONE: No issues found in the system.")
