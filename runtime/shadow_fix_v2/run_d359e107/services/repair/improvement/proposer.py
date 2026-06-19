"""
Self-Improvement: Proposer
Tespit edilen sorunlar için LLM tabanlı çözüm önerileri (diff) oluşturur.
"""
from typing import Dict, Any
from libs.llm.model_orchestrator import ModelOrchestrator
from services.observability.logging import get_logger

logger = get_logger("improvement.proposer")

class PatchProposer:
    def __init__(self, model_orch: ModelOrchestrator):
        self.model = model_orch

    async def propose_fix(self, issue: Dict[str, Any]) -> str:
        """Sorun için bir yama (patch) önerir."""
        reason = issue.get('reason') or issue.get('description') or "Bilinmeyen sorun"
        agent_id = issue.get('agent_id') or issue.get('evidence', {}).get('agent_id') or "system"
        evidence = issue.get('evidence') or "Kanıt yok"

        instruction_hint = issue.get('instruction_hint', "")
        hint_str = f"\n        STRATEJÄ°K TALÄ°MAT: {instruction_hint}\n" if instruction_hint else ""

        prompt = f"""
        Sistem Otopilot: Kendi Kendini Ä°yileÅŸtirme Modu
        Tespit Edilen Sorun: {reason}
        Ajan: {agent_id}
        KanÄ±tlar: {evidence}{hint_str}

        Sistemden alÄ±nan bu verilerle uzman bir mÃ¼hendis gibi davranarak sorunu kalÄ±cÄ± olarak Ã§Ã¶zmek iÃ§in bir aksiyon Ã¶ner.
        EÄŸer bir kod deÄŸiÅŸikliÄŸi gerekiyorsa, bunu standart DIFF formatÄ±nda sun.
        EÄŸer yapÄ±landÄ±rma deÄŸiÅŸikliÄŸi gerekiyorsa (timeout artÄ±rÄ±mÄ±, retry sayÄ±sÄ±nÄ± artÄ±rma vb.), bunu bir JSON objesi olarak 'config_patch' altÄ±nda belirt.

        Ã–nemli: Cevap sadece Ã§Ã¶zÃ¼m iÃ§ermeli.
        """
        try:
            response = await self.model.generate(prompt)
            return response
        except Exception as e:
            logger.error(f"PatchProposer error: {e}")
            return ""

# --- Singleton setup ---
from libs.llm.model_orchestrator import ModelOrchestrator
proposer = PatchProposer(ModelOrchestrator())
