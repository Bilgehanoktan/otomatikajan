import logging
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from core.agi.cognitive.synaptic_cortex import synaptic_cortex
from db.session import session_scope
from llm.model_orchestrator import ModelOrchestrator

_log = logging.getLogger("agi_thread_governor")

class ThreadGovernor:
    """
    [Katman 63] Thread Governor (Bilişsel Devamlılık Ünitesi).
    Proje bazlı bir 'İçsel Monolog' sürdürerek ajanların 'şimdi ne yapıyoruz ve neden' 
    sorusuna her adımda daha derin ve tutarlı yanıt vermesini sağlar.
    """

    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()

    async def get_active_thread(self, db: Any, project_id: str) -> str:
        """Projenin mevcut bilişsel durumunu ve monoloğunu getirir."""
        memories = await synaptic_cortex.search(
            db, 
            query="", 
            category="thought_thread", 
            project_id=project_id, 
            top_k=3
        )
        if not memories:
            return "Başlangıç aşaması. Stratejik temel atılıyor."
        
        # En yeniden en eskiye birleştir
        threads = [m['body'] for m in reversed(memories)]
        return "\n>>> ".join(threads)

    async def update_thread(self, db: Any, project_id: str, action_summary: str, outcome: str):
        """Eylem sonrası bilişsel durumu günceller ve 'Yansıma' (Reflection) yapar."""
        current_thread = await self.get_active_thread(db, project_id)
        
        prompt = f"""
        BİLİŞSEL YANSIMA (Egemen AGI)
        ----------------------------------------------
        PROJE: {project_id}
        MEVCUT MONOLOG: {current_thread}
        SON EYLEM: {action_summary}
        SONUÇ: {outcome}
        
        GÖREV: Bu son eylemi bilişsel monoloğa entegre et. 
        Sadece bir sonraki adımı etkileyecek en kritik çıkarımı ve 'şimdi nerede olduğumuzu' özetle.
        Yanıtı 1-2 cümlelik bir 'İçsel Monolog' (Thought Thread) olarak ver.
        """
        
        try:
            response = await self.model_orch.complete_task(
                agent_role="self_governor",
                prompt=prompt,
                system_prompt="Sen Sovereign AGI'nin içsel monoloğunu yöneten Thread Governor ünitesisin."
            )
            
            new_monologue = response.content.strip()
            
            await synaptic_cortex.save_thought_thread(
                db=db,
                thought=new_monologue,
                context_id=project_id
            )
            _log.info(f"[THREAD] Monolog güncellendi: {new_monologue[:100]}...")
            
        except Exception as e:
            _log.error(f"[THREAD-ERROR] Monolog güncelleme hatası: {e}")

# Singleton
thread_governor = ThreadGovernor()
