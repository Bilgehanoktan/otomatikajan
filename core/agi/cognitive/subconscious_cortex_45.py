"""
Semantic Dreamer (Phase 31) — Subconscious Memory Consolidation.
AGI'nin rölantideyken (idle) geçmiş tecrübeleri analiz ederek bilgi dikişi (stitching) 
ve kural sentezi (policy synthesis) yapmasını sağlayan birim.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from core.agi.schemas import EpisodeRecord
from db.models import Memory
from core.agi.cognitive.synaptic_cortex import synaptic_cortex
from llm.model_orchestrator import ModelOrchestrator
from observability.logging import get_logger

_log = get_logger("agi_subconscious_cortex")

class SubconsciousCortex45:
    """
    Korteks Ötesi Katman (Katman 45 - Sovereign): Bilişsel Konsolidasyon.
    Görevi: Kaotik tecrübe akışını (Episodes) yapısal 'Derin Bilgi'ye dönüştürmek (Sovereign v45).
    """
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()
        self.is_dreaming = False

    async def dream(self, db: AsyncSession, limit: int = 30):
        """
        Düşleme Döngüsü (Dream Cycle - v45).
        Sistemin bilinçaltı yansımasını tetikler.
        """
        if self.is_dreaming:
            _log.info("[SOVEREIGN-CORTEX] Zaten bir düşleme oturumu devam ediyor.")
            return

        self.is_dreaming = True
        _log.info("--- SOVEREIGN SUB-CONSCIOUS DREAMING BAŞLATILDI (v45.0) ---")
        
        try:
            # 1. Son bölümleri (Episodes) getir
            recent_episodes = await synaptic_cortex.get_recent(db, category="episode_record", limit=limit)
            if len(recent_episodes) < 5:
                _log.info("[SOVEREIGN-CORTEX] Konsolidasyon için yeterli veri yok.")
                return

            # --- A. Bilgelik Konsolidasyonu (Legacy consolidate_knowledge integrated) ---
            await self.consolidate_wisdom(db, recent_episodes)

            # --- B. Politika Sentezi ve Evrim Hazırlığı ---
            insights = await self.consolidate_episodes(recent_episodes)
            
            if insights:
                # Elde edilen 'Evrensel Dersleri' (Universal Lessons) kaydet
                for lesson in insights.get("universal_lessons", []):
                    await synaptic_cortex.save(
                        db,
                        agent_id="subconscious_cortex_45",
                        body=lesson["content"],
                        category="reflection_log",
                        importance=lesson.get("importance", 0.9),
                        tags=["universal", "dreamer_insight", "v45"],
                        metadata={"dream_id": str(datetime.now(timezone.utc).timestamp()), "version": "45.0"}
                    )
                
                redundant_ids = insights.get("redundant_episode_ids", [])
                if redundant_ids:
                    _log.info(f"[SOVEREIGN-CORTEX] {len(redundant_ids)} kayıt redundant olarak işaretleniyor.")
                    for r_id in redundant_ids:
                        try:
                            m = await db.get(Memory, r_id)
                            if m:
                                m.tags = list(set((m.tags or []) + ["consolidated_redundant"]))
                        except Exception:
                            pass
                
                for policy in insights.get("suggested_policies", []):
                    # Phase 46.3: Adversarial Policy Audit
                    audit_response = await self.model_orch.complete_task(
                        agent_role="critic",
                        prompt=f"Yeni Politika Önerisi: {policy['rule']}\nNeden: {policy['reason']}\n\nBu kural mantıklı mı? Güvenlik riski taşıyor mu? JSON: {{'is_valid': true/false, 'critique': '...'}}",
                        system_prompt="Sen AGI Politika Denetçisisin (Sovereign Critic)."
                    )
                    
                    import json, re
                    audit_match = re.search(r'\{.*\}', audit_response.content, re.DOTALL)
                    if audit_match and json.loads(audit_match.group()).get("is_valid"):
                        _log.info(f"[SOVEREIGN-CORTEX] Politika onaylandı: {policy['title']}")
                        await synaptic_cortex.save_policy(db, {
                            "title": f"Sovereign-Policy-v45: {policy['title']}",
                            "proposed_rule": policy["rule"],
                            "reason": policy["reason"],
                            "benefit": "Sovereign subconscious consolidation",
                            "evidence": [str(e.id) for e in recent_episodes[:3]]
                        })
                    else:
                        _log.warning(f"[SOVEREIGN-CORTEX] Politika REDDEDİLDİ: {policy['title']}")

            _log.info("--- SOVEREIGN DREAMING TAMAMLANDI (Derin Bilgi Sentezlendi) ---")

        except Exception as e:
            _log.error(f"[ERR] Sovereign Cortex döngüsü hatası: {e}")
        finally:
            self.is_dreaming = False

    async def consolidate_wisdom(self, db: AsyncSession, episodes: List[Any]):
        """
        Başarılı bölümlerden 'Global Çözüm Desenleri' (Wisdom) üretir.
        """
        successes = [e for e in episodes if e.metadata_.get("status") == "success"]
        if len(successes) < 3:
            return

        _log.info(f"[SOVEREIGN-CORTEX] {len(successes)} başarılı bölümden bilgelik süzülüyor...")
        
        history = "\n".join([f"- {e.metadata_.get('title')}: {e.body[:150]}" for e in successes])
        prompt = f"GÖREV GEÇMİŞİ:\n{history}\n\nLütfen bu başarılardan gelecekteki görevler için 'Global Çözüm Deseni' (Wisdom) üret.\nJSON: {{'pattern_name': '...', 'wisdom': '...', 'applicability': '...'}}"

        try:
            response = await self.model_orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt="Sen AGI Bilgelik Konsolidasyon (Sovereign Wisdom) ünitesisin."
            )
            import re
            import json
            match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if match:
                wisdom_data = json.loads(match.group())
                await synaptic_cortex.save(
                    db=db,
                    agent_id="subconscious_cortex_45",
                    body=wisdom_data.get("wisdom", ""),
                    category="semantic_wisdom",
                    importance=0.85,
                    metadata={
                        "pattern_name": wisdom_data.get("pattern_name", ""),
                        "applicability": wisdom_data.get("applicability", ""),
                        "source_episodes": [str(e.id) for e in successes],
                        "version": "45.0"
                    },
                    tags=["wisdom", "pattern", "v45"]
                )
        except Exception as e:
            _log.warning(f"[SOVEREIGN-CORTEX] Wisdom konsolidasyon hatası: {e}")

    async def consolidate_episodes(self, episodes: List[Any]) -> Dict[str, Any]:
        """
        LLM kullanarak bölümler arasındaki ortak noktaları (Patterns) bulur.
        """
        _log.info(f"[SOVEREIGN-CORTEX] {len(episodes)} bölüm konsolide ediliyor...")
        
        history_str = "\n".join([
            f"- Episode: {e.metadata_.get('title', 'N/A')} | Status: {e.metadata_.get('status', 'N/A')} | Summary: {e.body[:150]}"
            for e in episodes
        ])

        prompt = f"""
        SİSTEM GEÇMİŞİ (Sovereign Context v45):
        {history_str}
        
        GÖREV: Bu tecrübeler arasındaki ORTAK ÖRÜNTÜLERİ bul ve 'Evrensel Dersler' ile 'POLİTİKALAR' sentezle.
        Hangi hatalar otonomiyle çözülebilir? Hangi başarılar genel bir prensibe dönüşebilir?
        
        JSON formatında şu yapıda dön:
        {{
            "universal_lessons": [
                {{"content": "Evrensel ders açıklaması", "importance": 0.9}}
            ],
            "suggested_policies": [
                {{"title": "Politika Başlığı", "rule": "Kural tanımı", "reason": "Neden?", "impact": "0.8"}}
            ],
            "redundant_episode_ids": ["uuid_1", "uuid_2"]
        }}
        """

        system_prompt = (
            "Sen AGI Egemen Bilinçaltı Korteksi (Subconscious Cortex v45) bileşenisin. "
            "Görevin hiyerarşik veya zamansal veriden 'Bilinçaltı Konsolidasyonu' yaparak "
            "meta-bilgi (Meta-Knowledge) üretmektir."
        )

        try:
            response = await self.model_orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt=system_prompt
            )
            
            import re
            match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if match:
                import json
                return json.loads(match.group())
        except Exception as e:
            _log.warning(f"[SOVEREIGN-CORTEX] LLM konsolidasyon hatası: {e}")
            
        return {}

# Singleton instance
subconscious_cortex_45 = SubconsciousCortex45()
