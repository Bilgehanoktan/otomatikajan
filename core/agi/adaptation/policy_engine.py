import json
from typing import Optional, Dict, List, Any
from core.agi.schemas import EpisodeRecord, PolicyProposal
from llm.model_orchestrator import ModelOrchestrator
from memory.store import memory_store
from observability.logging import get_logger

_log = get_logger("agi_policy_engine")

class PolicyEngine:
    """
    Adaptation Core (Katman 8): Adaptive Policy Evolution.
    Geçmiş deneyimleri (özellikle başarısızlıkları) analiz ederek sistem geneli kurallar (Policy) üretir.
    """
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()

    async def evolve(self, db: Any) -> Optional[PolicyProposal]:
        """
        Son bölümleri analiz eder ve davranış değişikliği (Policy) önerir.
        """
        _log.info("Politika evrimi (Policy Evolution) analizi başlatılıyor...")
        
        # Son 15 bölümü getir
        recent_memories = await memory_store.get_recent(db, category="episode_record", limit=15)
        if not recent_memories:
            return None

        # Başarısızlıkları filtrele
        failures = [m for m in recent_memories if m.metadata_.get("status") == "failed"]
        if len(failures) < 2:
            _log.info("Yeterli başarısızlık deseni bulunamadı. Analiz durduruldu.")
            return None

        _log.info(f"{len(failures)} başarısızlık üzerine analiz yapılıyor...")

        # LLM'e analiz yaptır
        prompt = self._build_evolution_prompt(recent_memories)
        system_prompt = (
            "Sen bir AGI Adaptasyon Çekirdeği (Adaptation Core) bileşenisin. "
            "Sana verilen görev geçmişlerini analiz ederek, sistemin gelecekte aynı hataları "
            "yapmaması için 'Global Politikalar' veya 'Davranış Kuralları' üretmelisin. "
            "Öneri MUTLAKA yapısal JSON formatında olmalı."
        )

        try:
            response = await self.model_orch.complete_task(
                agent_role="strategist",
                prompt=prompt,
                system_prompt=system_prompt
            )
            
            policy_data = self._parse_json(response.content)
            if not policy_data:
                return None

            proposal = PolicyProposal(
                proposed_change=policy_data.get("proposed_rule", ""),
                reason=policy_data.get("reason", ""),
                expected_benefit=policy_data.get("expected_benefit", ""),
                supporting_evidence_episodes=[str(f.id) for f in failures],
                status="pending"
            )

            # Hafızaya kaydet
            await memory_store.save_policy(db, {
                "title": f"Auto-Policy: {proposal.proposed_change[:50]}...",
                "proposed_rule": proposal.proposed_change,
                "reason": proposal.reason,
                "benefit": proposal.expected_benefit,
                "evidence": proposal.supporting_evidence_episodes
            })
            
            _log.info(f"YENİ POLİTİKA ÖNERİSİ: {proposal.proposed_change}")
            return proposal

        except Exception as e:
            _log.error(f"Policy evolution hatası: {e}")
            return None

    def _build_evolution_prompt(self, memories: List[Any]) -> str:
        history = "\n".join([
            f"- Görev: {m.metadata_.get('title')} | Durum: {m.metadata_.get('status')} | Sonuç: {m.body[:200]}"
            for m in memories
        ])
        
        return f"""
        SİSTEM GEÇMİŞİ (Son 15 Görev):
        {history}
        
        Lütfen bu geçmişteki desenleri (özellikle başarısızlıkların ortak noktalarını) analiz et.
        Sistemin gelecekteki görevlerde uyması gereken YENİ BİR KURAL (Policy) öner.
        
        Örnek kural: "Python testleri çalıştırılırken her zaman PYTHONPATH çevre değişkeni set edilmelidir."
        
        JSON formatında yanıt ver:
        {{
            "proposed_rule": "Gelecekte uygulanacak kural",
            "reason": "Neden bu kurala ihtiyaç var?",
            "expected_benefit": "Bu kural neyi iyileştirecek?"
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
policy_engine = PolicyEngine()
