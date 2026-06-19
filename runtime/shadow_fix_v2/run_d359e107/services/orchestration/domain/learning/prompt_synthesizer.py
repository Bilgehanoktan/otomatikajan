import logging
import json
from typing import Dict, Any, List, Optional
from libs.llm.model_orchestrator import ModelOrchestrator

_log = logging.getLogger("agi_prompt_synthesizer")

class PromptSynthesizer:
    """
    Recursive Meta-Learning Engine (Phase 37).
    Analyzes agent performance and failure patterns to rewrite 'Agent Contracts'.
    """
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()

    async def refine_contract(self, agent_id: str, failure_logs: List[str], current_contract: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Gemi hatalardan ders kararak ajan talimatlarn (Prompt/Contract) optimize eder.
        """
        if not failure_logs:
            _log.info(f"[SYNTH] '{agent_id}' iin hata kayd yok, rafine edilmiyor.")
            return None

        _log.info(f"[SYNTH] '{agent_id}' iin meta-learning balatlyor. Hata says: {len(failure_logs)}")

        prompt = (
            f"Sen bir Meta-Learning Uzmansn. Grevin, '{agent_id}' rolndeki bir yapay zeka ajannn grev talimatlarn (Szleme) optimize etmek.\n\n"
            f"### MEVCUT SZLEME:\n{json.dumps(current_contract, indent=2, ensure_ascii=False)}\n\n"
            f"### GEM HATA DURUMLARI / DERSLER:\n" + "\n- ".join(failure_logs) + "\n\n"
            "### TALMAT:\n"
            "Yukardaki hatalar analiz et. Ajann bir daha ayn hatalar yapmamas iin 'Szleme'yi optimize et.\n"
            "Yantn SADECE geerli bir JSON objesi olmaldr.\n"
        )

        try:
            from libs.llm.model_orchestrator import ModelOrchestrator
            result = await self.model_orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt="Sen bir Meta-Learning Uzmanısın."
            )

            # Simple JSON parse attempt
            import re
            match = re.search(r'\{.*\}', result.content, re.DOTALL)
            if match:
                refined = json.loads(match.group())
                _log.info(f"[SYNTH] '{agent_id}' iin szleme otonom olarak optimize edildi.")
                return refined
            
            _log.warning(f"[SYNTH] '{agent_id}' iin szleme optimizasyonu baarsz.")
            return None

        except Exception as e:
            _log.error(f"[SYNTH] Meta-learning hatas: {e}")
            return None

prompt_synthesizer = PromptSynthesizer(None)
