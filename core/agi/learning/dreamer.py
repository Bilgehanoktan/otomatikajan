import json
from typing import List, Optional, Any, Dict
from core.agi.schemas import EpisodeRecord
from llm.model_orchestrator import ModelOrchestrator
from memory.store import memory_store
from sqlalchemy.ext.asyncio import AsyncSession
from observability.logging import get_logger

_log = get_logger("agi_dreamer")

class Dreamer:
    """
    Learning Core (Katman 13): Semantic Memory Consolidation.
    Geçmiş deneyimleri (Episodes) 'Semantik Bilgelik' (Wisdom) haline getirir.
    Sistemin her seferinde sıfırdan düşünmesini engeller.
    """
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()

    async def consolidate_knowledge(self, db: AsyncSession):
        """
        Başarılı bölümleri analiz eder ve 'En İyi Uygulama' (Best Practice) kuralları oluşturur.
        """
        _log.info("Semantik Rüya (Dreaming/Consolidation) başlatılıyor...")
        
        # Son 20 başarılı bölümü getir
        recent_episodes = await memory_store.get_recent(db, category="episode_record", limit=20)
        successes = [e for e in recent_episodes if e.metadata_.get("status") == "success"]
        
        if len(successes) < 3:
            _log.info("Yeterli başarılı desen yok. Konsolidasyon durduruldu.")
            return

        # LLM'e analiz yaptır
        prompt = self._build_consolidation_prompt(successes)
        system_prompt = (
            "Sen bir AGI Semantik Konsolidasyon (Dreamer) bileşenisin. "
            "Sana verilen başarılı görev geçmişlerini analiz ederek, gelecekteki görevlerde "
            "hız ve başarıyı artıracak 'Global Çözüm Desenleri' üretmelisin."
        )

        try:
            response = await self.model_orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt=system_prompt
            )
            
            wisdom_data = self._parse_json(response.content)
            if not wisdom_data:
                return

            # Belleğe semantik bilgelik olarak kaydet
            await memory_store.save(
                db=db,
                agent_id="dreamer",
                body=wisdom_data.get("wisdom", ""),
                category="semantic_wisdom",
                importance=0.8,
                metadata={
                    "pattern_name": wisdom_data.get("pattern_name", ""),
                    "applicability": wisdom_data.get("applicability", ""),
                    "source_episodes": [str(e.id) for e in successes]
                },
                tags=["wisdom", "pattern"]
            )
            _log.info(f"YENİ BİLGELİK (Wisdom) KAYDEDİLDİ: {wisdom_data.get('pattern_name')}")

        except Exception as e:
            _log.error(f"Dreaming hatası: {e}")

    def _build_consolidation_prompt(self, episodes: List[Any]) -> str:
        history = "\n".join([
            f"- Görev: {e.metadata_.get('title')} | Çözüm Yolu: {e.body[:200]}"
            for e in episodes
        ])
        
        return f"""
        BAŞARILI GÖREV GEÇMİŞİ:
        {history}
        
        Lütfen bu başarıların ortak paydalarını ve en etkili çözüm desenlerini analiz et.
        Müstakbel görevlerde 'Playbook' olarak kullanılabilecek YENİ BİR BİLGELİK (Global Pattern) tanımla.
        
        JSON formatında yanıt ver:
        {{
            "pattern_name": "Desen İsmi (Kısa)",
            "wisdom": "Detaylı çözüm stratejisi ve uygulama rehberi",
            "applicability": "Hangi durumlarda uygulanmalıdır?"
        }}
        """

    def _parse_json(self, content: str) -> Optional[Dict[str, Any]]:
        try:
            import re
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception:
            pass
        return None

# --- Singleton ---
dreamer = Dreamer()
