"""
Evolution Engine (Phase 37) — Policy-to-Code Translation.
Otonom olarak sentezlenen politikaları (Policies) somut kod değişikliklerine 
dönüştüren ve 'Self-Patching' sürecini başlatan birim.
"""
import os
import json
from typing import List, Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import Memory
from core.agi.schemas import PolicyProposal
from core.agi.operational.patching_sandbox import patching_sandbox
from core.agi.security.audit_gate import audit_gate # Faz 38
from core.agi.monitoring.provenance_engine_45 import provenance_engine_45
from llm.model_orchestrator import ModelOrchestrator
from observability.logging import get_logger

_log = get_logger("agi_sovereign_evolution")

class SovereignEvolution45:
    """
    Öğrenme ve Adaptasyonun Zirvesi (Katman 45 - Sovereign): Kendi Kodunu Dönüştürme.
    """
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()

    async def evolve_system(self, db: AsyncSession):
        """
        Adaptasyon Döngüsü (Evolution Cycle - v45).
        Bekleyen politikaları tarar ve uygulanabilir olanları yamaya çevirir.
        """
        _log.info("--- SOVEREIGN EVOLUTION DÖNGÜSÜ BAŞLATILDI (v45.0) ---")
        
        # 1. Bekleyen politikaları (Policy Proposals) getir
        stmt = select(Memory).where(Memory.category == "policy_proposal").order_by(Memory.created_at)
        result = await db.execute(stmt)
        memories = result.scalars().all()
        
        pending_policies = []
        for m in memories:
            if m.metadata_.get("status") == "pending":
                pending_policies.append(m)

        if not pending_policies:
            _log.info("[SOVEREIGN-EVO] Bekleyen politika (Policy) bulunamadı.")
            return

        for m_policy in pending_policies:
            _log.info(f"[SOVEREIGN-EVO] İşlenen politika: {m_policy.metadata_.get('title')}")
            
            # 2. Politikayı Kod Değişikliğine Çevir
            patch_insight = await self.generate_patch_insight(m_policy)
            
            if not patch_insight:
                continue

            target_file = patch_insight.get("file_path")
            new_code = patch_insight.get("new_content")

            # 3. Güvenlik Denetimi (Audit Gate - Regression Testing) (Faz 38)
            is_safe = await audit_gate.verify_self_patch(
                target_file, 
                new_code, 
                reason=m_policy.metadata_.get("proposed_rule", "")
            )

            if is_safe:
                # --- Faz 41.2: Capture for Provenance ---
                original_content = ""
                if os.path.exists(target_file):
                    with open(target_file, "r", encoding="utf-8") as f:
                        original_content = f.read()

                # 4. Patching Sandbox ile Uygula (Faz 36)
                result = patching_sandbox.apply_atomic_patch(target_file, new_code)
                
                if result["success"]:
                    # --- Faz 41.2: Record Provenance ---
                    await provenance_engine_45.record_evolution_step(
                        db=db,
                        file_path=target_file,
                        original_content=original_content,
                        new_content=new_code,
                        policy_id=str(m_policy.id),
                        reason=m_policy.metadata_.get("reason", "Autonomous evolution")
                    )

                    # Politikayı 'active' yap
                    m_policy.metadata_ = {**m_policy.metadata_, "status": "active", "applied_patch": result["backup"], "evolution_version": "45.0"}
                    _log.info(f"[SOVEREIGN-EVO] Yama BAŞARIYLA uygulandı ve Provenance kaydedildi: {target_file}")
                else:
                    m_policy.metadata_ = {**m_policy.metadata_, "status": "failed", "error": result["error"]}
                    _log.error(f"[SOVEREIGN-EVO] Yama BAŞARISIZ: {result['error']}")

        await db.commit()
        _log.info("--- SOVEREIGN EVOLUTION DÖNGÜSÜ TAMAMLANDI ---")

    async def generate_patch_insight(self, m_policy: Memory) -> Dict[str, Any]:
        """
        LLM ile politika tanımını somut dosya değişikliğine (file_path, new_content) dönüştürür.
        """
        rule = m_policy.metadata_.get("proposed_rule", "")
        reason = m_policy.metadata_.get("reason", "")
        
        _log.info(f"[SOVEREIGN-EVO] Yama sentezleniyor (LLM): {rule[:50]}...")

        prompt = f"""
        POLİTİKA (Policy): {rule}
        NEDEN (Reason): {reason}
        
        GÖREV: Bu yeni kuralı sisteme OTONOM YAMA olarak uygulaman gerekiyor. (v45 SOVEREIGN)
        Lütfen bu kuralın uygulanması gereken dosyayı bul ve dosyanın TAM YENİ İÇERİĞİNİ üret.
        
        JSON formatında şu yapıda dön:
        {{
            "file_path": "dosya/yolu.py",
            "new_content": "Dosyanın tam yeni içeriği buraya gelecektir...",
            "safety_assessment": "Yamanın güvenliği üzerine kısa not"
        }}
        """

        system_prompt = (
            "Sen AGI Egemen Evrim Motoru (Sovereign Evolution Engine v45) bileşenisin. "
            "Görevin, sözel politikaları somut kaynak kodu yamalarına dönüştürmektir."
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
                return json.loads(match.group())
        except Exception as e:
            _log.warning(f"[SOVEREIGN-EVO] Patch sentez hatası: {e}")
        
        return {}

# Singleton instance
sovereign_evolution_45 = SovereignEvolution45()
