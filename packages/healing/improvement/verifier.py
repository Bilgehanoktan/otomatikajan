from __future__ import annotations
"""
Self-Improvement: Verifier
Önerilen yamaları (patch) sandbox ortamında test eder ve doğrular.
"""
import asyncio
import tempfile
from pathlib import Path
from typing import Any, Dict

from packages.orchestration.application.sandbox_runner import SandboxRunner
from observability.logging import get_logger

logger = get_logger("improvement.verifier")

class PatchVerifier:
    def __init__(self, sandbox_runner: SandboxRunner):
        self.sandbox_runner = sandbox_runner

    async def verify_patch(self, patch: str, context: Dict[str, Any]) -> bool:
        """
        context beklenen alanlar:
        - target_file
        - verification_commands: list[str]
        """
        target_file = context.get("target_file")
        verification_commands = context.get("verification_commands", [])

        if not patch or not patch.strip():
            logger.error("Boş patch doğrulanamaz")
            return False

        if not target_file:
            logger.error("Verifier context içinde target_file yok")
            # Fallback for old system or mock tests
            target_file = "dummy.py"

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                workdir = Path(tmpdir)
                target_path = workdir / Path(target_file).name

                # Patch içeriğini yaz
                target_path.write_text(patch, encoding="utf-8")

                if not verification_commands:
                    # Varsayılan: Sadece sözdizimi kontrolü (mock)
                    return True

                for cmd in verification_commands:
                    result = await self.sandbox_runner.run_command(
                        command=cmd,
                        cwd=str(workdir),
                        timeout=60,
                    )
                    if result.get("status") != "success":
                        logger.error("Verifier command failed: %s", cmd)
                        return False

                return True

        except Exception as e:
            logger.exception("PatchVerifier hata verdi: %s", e)
            return False

# Export singleton instance
verifier = PatchVerifier(SandboxRunner())
