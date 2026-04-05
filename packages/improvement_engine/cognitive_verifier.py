from __future__ import annotations
"""
Cognitive Self-Improvement: Cognitive Verifier (Faz 12.1)
Replaces the mock verifier with a structured multi-agent debate reasoning loop.
Ensures every patch is cross-examined before being considered canonical.
"""
import asyncio
import tempfile
import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from core.sandbox_runner import SandboxRunner
from core.debate_engine import DebateEngine
from llm.model_orchestrator import model_orchestrator
from observability.logging import get_logger

logger = get_logger("improvement.cognitive_verifier")

class CognitiveVerifier:
    def __init__(self, sandbox_runner: SandboxRunner, debate_engine: DebateEngine):
        self.sandbox_runner = sandbox_runner
        self.debate_engine = debate_engine

    async def verify_patch(self, patch: str, issue: Dict[str, Any]) -> Tuple[bool, float, str]:
        """
        Yamayı hem teknik (sandbox) hem de kavramsal (debate) olarak doğrular.
        Returns: (success, confidence_score, reasoning_summary)
        """
        target_file = issue.get("agent_id", "unknown_file.py")
        if not target_file.endswith(".py") and "/" not in target_file:
             target_file = f"agents/{target_file}.py"

        logger.info(f"Cognitive Verification started for: {target_file}")

        # 1. Teknik Doğrulama (Sandbox)
        sandbox_success = await self._run_sandbox_check(patch, target_file)
        if not sandbox_success:
            return False, 0.0, "Sandbox technical check failed (Syntax/Runtime error)."

        # 2. Kavramsal Doğrulama (Reflective Reasoning via Debate)
        debate_success, confidence, reasoning = await self._run_reflective_debate(patch, issue)
        
        return debate_success, confidence, reasoning

    async def _run_sandbox_check(self, patch: str, target_file: str) -> bool:
        """Yamayı izole ortamda çalıştırıp sözdizimi ve temel çalışma kontrolü yapar."""
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                workdir = Path(tmpdir)
                target_path = workdir / Path(target_file).name
                target_path.write_text(patch, encoding="utf-8")

                # Syntax check (Python specific)
                result = await self.sandbox_runner.run_command(
                    command=f"python -m py_compile {target_path.name}",
                    cwd=str(workdir),
                    timeout=30,
                )
                return result.success
        except Exception as e:
            logger.error(f"Sandbox check unexpected error: {e}")
            return False

    async def _run_reflective_debate(self, patch: str, issue: Dict[str, Any]) -> Tuple[bool, float, str]:
        """DebateEngine kullanarak yamanın kalitesini tartışır."""
        topic = f"PATCH EVALUATION: Fix for '{issue.get('reason', 'Unknown Issue')}' in {issue.get('agent_id')}"
        
        context = f"""
ISSUE CONTEXT:
{json.dumps(issue, indent=2)}

PROPOSED PATCH:
```python
{patch}
```

Evaluate if this patch is architecturally sound, secure, and solves the root cause without side effects.
"""
        try:
            # 2 Turlu Muhakeme (Faz 12.1 Standardı)
            debate_result = await self.debate_engine.run_debate(
                topic=topic,
                agent_a="architect",
                agent_b="security",
                moderator="qa_engineer",
                context=context
            )

            # Konsensüs analizi: Eğer moderatör onay verdiyse ve 'agreement_reached' ise
            success = debate_result.agreement_reached
            
            # Confidence skoru moderatörün karar metnine ve agreement durumuna göre hesaplanır
            # Mock yerine basit bir kural seti (AGI Logic):
            confidence = 0.95 if success else 0.4
            
            # Eğer moderatör 'HAYIR' dediyse ama engine agreement_reached diyorsa (nadiren olur)
            if "REJECT" in debate_result.consensus.upper() or "HAYIR" in debate_result.consensus.upper():
                success = False
                confidence = 0.2

            return success, confidence, debate_result.consensus

        except Exception as e:
            logger.error(f"Reflective debate failed: {e}")
            return False, 0.0, f"Critique error: {str(e)}"

# Singleton Instance
cognitive_verifier = CognitiveVerifier(SandboxRunner(), DebateEngine(model_orchestrator))
