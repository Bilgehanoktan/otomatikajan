import json
from typing import Optional, Dict, Any
from core.agi.schemas import EpisodeRecord, VerificationReport
from llm.model_orchestrator import ModelOrchestrator
from observability.logging import get_logger

_log = get_logger("agi_memory_gate")

class MemoryGate:
    """
    Learning Core (Katman 7.7): Memory Write Gate (Hafıza Yazım Kapısı).
    Her deneyimin (Episode) kalıcı hafızaya (Synaptic Cortex) yazılmaya 
    değer olup olmadığını denetleyen bilişsel filtredir.
    """
    
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()
        self.threshold_score = 0.6  # Yazım için minimum gerçeklik/güven skoru

    async def evaluate_eligibility(self, episode: EpisodeRecord) -> bool:
        """
        Episode kaydının kalıcı hafızaya alınabilirliğini test eder.
        """
        _log.info(f"[MEMORY-GATE] '{episode.episode_id}' için yazım uygunluğu test ediliyor...")

        # 1. Temel Metrik Denetimi
        if not episode.verification:
            _log.warning("[MEMORY-GATE] Doğrulama raporu eksik. Reddedildi.")
            return False

        # Gerçeklik Puanı (Integration Reality Score)
        reality = episode.verification.integration_reality_score
        confidence = episode.verification.confidence_adjusted
        
        # 2. Heuristic Red Reddetme
        if not episode.verification.result_status and not episode.lessons_learned:
            _log.info("[MEMORY-GATE] Başarısız ve ders içermeyen episode. Reddedildi.")
            return False

        # 3. LLM Destekli Bilişsel Değerlendirme (Opsiyonel: Yüksek Belirsizlik Durumunda)
        if 0.4 <= reality <= 0.7:
             _log.info("[MEMORY-GATE] Sınırda skor. Bilişsel denetim başlatılıyor...")
             is_valuable = await self._cognitive_value_check(episode)
             if not is_valuable:
                 _log.info("[MEMORY-GATE] Bilişsel denetim başarısız. Reddedildi.")
                 return False

        # 4. Final Karar
        final_score = (reality * 0.7) + (confidence * 0.3)
        if final_score >= self.threshold_score:
            _log.info(f"[MEMORY-GATE] Kabul edildi. Skor: {final_score:.2f}")
            episode.verification.safe_to_learn = True
            return True
        
        _log.warning(f"[MEMORY-GATE] Reddedildi. Yetersiz skor: {final_score:.2f}")
        return False

    async def _cognitive_value_check(self, ep: EpisodeRecord) -> bool:
        """
        LLM kullanarak deneyimin 'öğrenilebilir değer' taşıyıp taşımadığını anlar.
        """
        prompt = f"""
        Aşağıdaki görev deneyimini (Episode) incele. 
        Bu deneyim, sistemin gelecekteki kararlarını iyileştirecek bir 'ders' veya 'pattern' içeriyor mu?
        Yoksa sadece gürültü (noise) mü?
        
        GÖREV: {ep.problem_frame.objective if ep.problem_frame else 'N/A'}
        SONUÇ: {ep.final_output[:500] if ep.final_output else 'N/A'}
        HATALAR: {ep.lessons_learned}
        
        Yanıtını JSON olarak ver:
        {{ "is_worthy": true/false, "reason": "nedeni" }}
        """
        
        try:
            response = await self.model_orch.complete_task(
                agent_role="critic",
                prompt=prompt,
                system_prompt="Sen bir AGI Hafıza Denetçisisin (Memory Auditor). Sadece değerli ve doğrulanmış bilgilerin sisteme dâhil edilmesini sağlarsın."
            )
            data = json.loads(response.content) if "{" in response.content else {"is_worthy": False}
            return data.get("is_worthy", False)
        except Exception as e:
            _log.error(f"Cognitive value check failed: {e}")
            return False

# Singleton
memory_gate = MemoryGate()
