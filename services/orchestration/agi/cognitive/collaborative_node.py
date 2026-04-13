import logging
from typing import Dict, Any, List, Optional
from libs.llm.model_orchestrator import ModelOrchestrator

_log = logging.getLogger("agi_collaborative_node")

class CollaborativeNode:
    """
    Cognitive Layer 35: Collaborative Reasoning Protocol (Bilişsel İşbirliği Protokolü).
    Ajanların görev sırasında diğer uzmanlara danışmasını (Peer-to-Peer Consultation) sağlar.
    """

    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()

    async def consult(self, 
                      requesting_agent: str, 
                      target_specialist: str, 
                      current_work: str, 
                      question: str) -> str:
        """
        Bir ajanın diğerine spesifik bir konuda danışmasını sağlar.
        """
        _log.info(f"[COLLABORATION] {requesting_agent} -> {target_specialist} danışma talebi.")
        
        prompt = f"""
        DANIŞAN AJAN: {requesting_agent}
        MEVCUT ÇALIŞMA:
        {current_work[:1000]}...
        
        SORU / BELİRSİZLİK:
        {question}
        
        SAYIN {target_specialist.upper()}, lütfen yukarıdaki soruya kendi uzmanlık alanın çerçevesinde 
        KESİN, TEKNİK ve UYGULANABİLİR bir yanıt ver. Eğer bir risk görüyorsan açıkça belirt.
        """
        
        try:
            response = await self.model_orch.complete_task(
                agent_role=target_specialist,
                prompt=prompt,
                system_prompt=f"Sen bir İşbirlikçi Uzman (Collaborative Expert) birimisin. {requesting_agent} adlı ajana teknik destek sağlıyorsun."
            )
            return response.content
        except Exception as e:
            _log.error(f"[COLLABORATION] Danışma hatası: {e}")
            return "Üzgünüm, şu an teknik bir kısıt nedeniyle yanıt veremiyorum. Mevcut en güvenli yoldan devam et."

# Singleton
collaborative_node = CollaborativeNode()
