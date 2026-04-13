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

        prompt = f"""
        Sistem Otopilot: Kendi Kendini İyileştirme Modu
        Tespit Edilen Sorun: {reason}
        Ajan: {agent_id}
        Kanıtlar: {evidence}
        
        Sistemden alınan bu verilerle uzman bir mühendis gibi davranarak sorunu kalıcı olarak çözmek için bir aksiyon öner. 
        Eğer bir kod değişikliği gerekiyorsa, bunu standart DIFF formatında sun.
        Eğer yapılandırma değişikliği gerekiyorsa (timeout artırımı, retry sayısını artırma vb.), bunu bir JSON objesi olarak 'config_patch' altında belirt.

        Önemli: Cevap sadece çözüm içermeli.
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
