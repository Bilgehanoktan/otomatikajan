import json
import logging
from typing import List, Dict, Any, Optional
from llm.model_orchestrator import ModelOrchestrator
from core.agi.cognitive.synaptic_cortex import synaptic_cortex

_log = logging.getLogger("agi_knowledge_distiller")

class KnowledgeDistiller:
    """
    Learning Layer 35: Knowledge Distillation (Bilişsel Damıtma).
    Dağınık bellek kayıtlarını 'Sistem İçgüdülerine' (System Instincts) dönüştürür.
    """

    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()

    async def distill_instincts(self, episodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Başarılı ve başarısız örneklerden genel kurallar ve paternler çıkarır.
        """
        if len(episodes) < 2:
            _log.info("[DISTILLER] Yetersiz veri (en az 2 bölüm gerekli).")
            return []

        _log.info(f"[DISTILLER] {len(episodes)} bölüm üzerinden damıtma (distillation) başlatılıyor...")
        
        # Bölüm özetlerini topla
        summaries = "\n".join([
            f"- EPISODE ({e.get('episode_id')}): {e.get('final_output', '')[:300]}"
            for e in episodes
        ])

        prompt = f"""
        Aşağıdaki deneyim kayıtlarını (Episodes) incele. 
        Bunlar arasından 'Sistem Genelinde' geçerli olabilecek 3-5 adet teknik kural veya stratejik patern çıkar.
        
        DENEYİMLER:
        {summaries}
        
        Yanıtı JSON formatında (Instinct) ver:
        {{
            "instincts": [
                {{
                    "title": "Kısa başlık",
                    "pattern": "Teknik veya stratejik kural/patern",
                    "confidence": 0.85,
                    "category": "security/performance/logic"
                }}
            ]
        }}
        """

        try:
            response = await self.model_orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt="Sen bir AGI Bilişsel Bilgi Sentezleyicisisin. Dağınık verilerden sistem için 'Kalıcı İçgüdüler' üretirsin."
            )
            
            data = self._parse_json(response.content)
            instincts = data.get("instincts", [])
            
            for inst in instincts:
                _log.info(f"[DISTILLER] Yeni sistem içgüdüsü damıtıldı: {inst['title']}")
                # SynapticCortex'e 'instinct' kategorisinde kaydet
                await synaptic_cortex.save(
                    db=None, # UGC Hot Cache
                    agent_id="distiller",
                    body=f"{inst['title']}: {inst['pattern']}",
                    category="system_instinct",
                    importance=inst.get("confidence", 0.8),
                    metadata={"instinct_category": inst.get("category")}
                )
            
            return instincts

        except Exception as e:
            _log.error(f"[DISTILLER] Damıtma hatası: {e}")
            return []

    def _parse_json(self, text: str) -> Optional[Dict]:
        import re
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
        return None

# Singleton
knowledge_distiller = KnowledgeDistiller()
