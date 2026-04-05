import asyncio
import subprocess
import os
from typing import Dict, Any, List, Optional
from observability.logging import get_logger

_log = get_logger("agi_symbolic_engine")

class SymbolicEngine:
    """
    Sembolik Doğrulama Motoru (Symbolic Engine).
    Kodun mantıksal, tip ve güvenlik doğruluğunu ruff, bandit ve mypy kullanarak
    resmi (symbolic) kurallarla denetler.
    """
    
    async def run_safety_scans(self, file_path: str) -> Dict[str, Any]:
        """Tüm sembolik denetimleri çalıştırır."""
        _log.info(f"[SYMBOLIC] Dosya taranıyor: {file_path}")
        
        results = {
            "is_valid": True,
            "ruff_errors": [],
            "bandit_risks": [],
            "mypy_type_errors": [],
            "score": 1.0
        }
        
        # 1. Ruff (Linter & Anti-Patterns)
        ruff_ok, ruff_out = await self._run_tool(["python", "-m", "ruff", "check", "--no-cache", file_path])
        if not ruff_ok:
            results["is_valid"] = False
            results["ruff_errors"] = self._parse_lines(ruff_out)
        
        # 2. Bandit (Security)
        bandit_ok, bandit_out = await self._run_tool(["python", "-m", "bandit", "-r", "-q", file_path])
        if not bandit_ok:
            results["is_valid"] = False
            results["bandit_risks"] = self._parse_lines(bandit_out)
            
        # 3. Mypy (Type-Safety)
        mypy_ok, mypy_out = await self._run_tool(["python", "-m", "mypy", "--ignore-missing-imports", file_path])
        if not mypy_ok:
            results["is_valid"] = False
            results["mypy_type_errors"] = self._parse_lines(mypy_out)

        # Skor Hesaplama
        penalty = (len(results["ruff_errors"]) * 0.1) + \
                  (len(results["bandit_risks"]) * 0.3) + \
                  (len(results["mypy_type_errors"]) * 0.2)
        results["score"] = max(0.0, 1.0 - penalty)
        
        return results

    async def _run_tool(self, cmd: List[str]) -> (bool, str):
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            output = stdout.decode().strip() or stderr.decode().strip()
            return process.returncode == 0, output
        except Exception as e:
            return False, str(e)

    def _parse_lines(self, output: str) -> List[str]:
        if not output: return []
        return [line.strip() for line in output.split("\n") if line.strip()]

# Singleton
symbolic_engine = SymbolicEngine()
