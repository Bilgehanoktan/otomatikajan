import os
import json
from typing import Optional, Dict, List, Any
from llm.model_orchestrator import ModelOrchestrator
from core.agi.cognitive.synaptic_cortex import synaptic_cortex as memory_store
from sqlalchemy.ext.asyncio import AsyncSession
from observability.logging import get_logger

_log = get_logger("agi_prompt_optimizer")

class PromptOptimizer:
    """
    Adaptation Core (Katman 14): Recursive Prompt Self-Optimization.
    Ajanların (Specialists) performans istatistiklerini izler ve kurallarını (System Prompts) otonom optimize eder.
    """
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()
        self.dynamic_prompts_path = os.path.join("agents", "dynamic_prompts.json")

    async def adapt_specialists(self, db: AsyncSession):
        """
        Başarısızlığı yüksek ajanların sistem promptlarını iyileştirir.
        """
        _log.info("Ajan Düşünce Yapısı (System Prompt) Optimizasyonu başlatılıyor...")
        
        # Son 50 bölümü analiz et
        recent_memories = await memory_store.get_recent(db, category="episode_record", limit=50)
        
        # Ajan bazlı hata metriği
        agent_failures: Dict[str, list] = {}
        for mem in recent_memories:
            status = mem.metadata_.get("status")
            if status == "failed":
                # Basitçe hatada geçen ajanı bul (bu veri SkillLogRepository veya Episode metadata'dan gelmelidir)
                # Şimdilik örnek ajan listesi üzerinden geçelim
                pass
        
        # ÖRNEK: Eğer bir ajan (örn: backend_dev) son 3 görevde başarısızsa, promptunu optimize et
        # TODO: Gerçek metrik entegrasyonu. Şimdilik potansiyel 'Problematic' ajanları belirle.
        problematic_agents = ["backend_dev", "qa_engineer"] # Simülasyon veri

        for agent_id in problematic_agents:
            await self._evolve_prompt(agent_id, db)

    async def _evolve_prompt(self, agent_id: str, db: AsyncSession):
        """Belirli bir ajan için yeni bir uzmanlık promptu sentezler."""
        _log.info(f"Ajan Promptu Evrimleşiyor: {agent_id}")
        
        # Ajanın geçmiş hatalarını getir
        recent_errors = await memory_store.get_recent(db, category="episode_record", limit=5)
        error_context = "\n".join([f"- Hata: {e.body[:200]}" for e in recent_errors if e.metadata_.get("status") == "failed"])
        
        prompt = f"""
        Uzman Ajan: {agent_id}
        Son Zamanlardaki Hatalar:
        {error_context}
        
        Lütfen bu ajanın sistem promptunu (talimatlarını), bu hataları bir daha yapmayacak şekilde 
        DAHA SAVUNMACI (Defensive) ve AYRINTILI (Detailed) hale getirerek YENİDEN YAZ.
        
        JSON formatında yanıt ver:
        {{
            "agent_id": "{agent_id}",
            "new_system_prompt": "Yeni iyileştirilmiş prompt metni",
            "reasoning": "Neden bu değişiklikler yapıldı?"
        }}
        """
        
        try:
            response = await self.model_orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt="Sen bir AGI Bilişsel Tasarım Uzmanısın (Cognitive Architect)."
            )
            
            evolution_data = self._parse_json(response.content)
            if not evolution_data:
                return

            self._save_dynamic_prompt(agent_id, evolution_data.get("new_system_prompt", ""))
            _log.info(f"AJAN PROMPTU GÜNCELLENDİ (L14): {agent_id}")

        except Exception as e:
            _log.error(f"Prompt evrimi hatası: {e}")

    def _save_dynamic_prompt(self, agent_id: str, prompt: str):
        """Yeni promptu kalıcı dosyaya kaydeder."""
        try:
            prompts = {}
            if os.path.exists(self.dynamic_prompts_path):
                with open(self.dynamic_prompts_path, "r", encoding="utf-8") as f:
                    prompts = json.load(f)
            
            prompts[agent_id] = prompt
            
            with open(self.dynamic_prompts_path, "w", encoding="utf-8") as f:
                json.dump(prompts, f, indent=4, ensure_ascii=False)
        except Exception as e:
            _log.error(f"Prompt kaydetme hatası: {e}")

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
prompt_optimizer = PromptOptimizer()
