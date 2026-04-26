from __future__ import annotations
"""
Self-Improvement: Verifier
Önerilen yamaları (patch) sandbox ortamında test eder ve doğrular.
"""
import asyncio
import tempfile
from pathlib import Path
from typing import Any, Dict

from services.orchestration.application.sandbox_runner import SandboxRunner
from services.observability.logging import get_logger

logger = get_logger("improvement.verifier")

class PatchVerifier:
    def __init__(self, sandbox_runner: SandboxRunner):
        self.sandbox_runner = sandbox_runner

    async def verify_patch(self, patch: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        GeliÅŸmiÅŸ doÄŸrulama: Ã–nce Axiology (Etik/GÃ¼venlik), sonra Sandbox.
        """
        from services.orchestration.agi.cognitive.axiology_engine import axiology_engine

        target_file = context.get("target_file", "core/orchestrator.py")
        logger.info(f"Yama doÄŸrulanÄ±yor: {target_file}")

        # 1. Axiology Denetimi (BiliÅŸsel Bariyer)
        audit = await axiology_engine.evaluate_alignment(patch, context="improvement_patch")
        if audit.get("decision") == "reject":
            logger.error(f"Axiology reddetti: {audit.get('rejection_reason')}")
            return {"success": False, "reason": "axiology_reject", "audit": audit}

        if audit.get("decision") == "flag":
            logger.warning(f"Axiology uyardÄ±: {audit.get('justification')}")
            # EÄŸer corrective_action varsa, Gate bunu kullanarak tekrar deneyebilir
            if audit.get("corrective_action"):
                return {"success": False, "reason": "axiology_retry_suggested", "audit": audit}

        # 2. Sandbox Testi (Teknik Bariyer)
        if not patch or not patch.strip():
            return {"success": False, "reason": "empty_patch"}

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                workdir = Path(tmpdir)
                target_path = workdir / Path(target_file).name
                target_path.write_text(patch, encoding="utf-8")

                verification_commands = context.get("verification_commands", [])
                if not verification_commands:
                    return {"success": True, "audit": audit}

                for cmd in verification_commands:
                    result = await self.sandbox_runner.run_command(
                        command=cmd,
                        cwd=str(workdir),
                        timeout=60,
                    )
                    if result.get("status") != "success":
                        logger.error("Verifier command failed: %s", cmd)
                        return {"success": False, "reason": "test_failure", "cmd": cmd}

                return {"success": True, "audit": audit}

        except Exception as e:
            logger.exception("PatchVerifier hata verdi: %s", e)
            return False

# Export singleton instance
verifier = PatchVerifier(SandboxRunner())
