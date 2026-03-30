from typing import Optional, List, Dict, Any
from memory.store import memory_store
from db.session import session_scope
from observability.logging import get_logger

_log = get_logger("agi_knowledge_bridge")

class GlobalKnowledgeBridge:
    """
    Learning Core (Katman 7): Cross-Domain Knowledge Transfer.
    Farklı projeler arasında bilgi köprüsü kurar.
    """
    def __init__(self):
        self.local_project_id: Optional[str] = None

    def set_current_project(self, project_id: str):
        self.local_project_id = project_id

    async def retrieve_universal_solution(self, problem_description: str) -> List[Dict[str, Any]]:
        """
        Tüm projeler genelinde (Global) bir çözüm arar.
        """
        _log.info(f"Evrensel çözüm aranıyor: {problem_description[:50]}...")
        
        async with session_scope() as db:
            # project_id=None vererek global arama yapıyoruz
            results = await memory_store.search(
                db=db,
                query=problem_description,
                category="episode_record",
                project_id=None, 
                top_k=5
            )
            
            # Kendi projesinden olmayan sonuçları filtreleyebilir veya işaretleyebiliriz
            findings = []
            for res in results:
                is_external = res.get("project_id") != self.local_project_id
                findings.append({
                    "body": res["body"],
                    "is_cross_domain": is_external,
                    "confidence": res["score"]
                })
            
            return findings

    async def bridge_knowledge(self, source_episode_id: str, target_project_id: str):
        """
        Belirli bir 'Episode'u başka bir projeye 'Skill' olarak transfer eder.
        """
        _log.info(f"Bilgi köprüsü kuruluyor: {source_episode_id} -> {target_project_id}")
        # Bu kısımda Distiller ile entegre çalışarak soyutlama yapılır.
        pass

# Singleton
knowledge_bridge = GlobalKnowledgeBridge()
