import asyncio
import uuid
import os
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .sovereign_auditor import sovereign_auditor
from services.repair.improvement.proposer import proposer
from services.repair.improvement.cognitive_verifier import cognitive_verifier
from services.orchestration.agi.operational.patching_sandbox import patching_sandbox
from services.orchestration.agi.security.audit_gate import audit_gate
from services.orchestration.agi.monitoring.provenance_engine_45 import provenance_engine_45
from libs.db.models import Memory
from services.orchestration.agi.learning.specialist_forge import specialist_forge
from services.orchestration.agi.schemas import EpisodeRecord, CausalGraph
from services.orchestration.domain.events import event_bus
from services.observability.logging import get_logger

logger = get_logger("agi.cognitive.evolution")

class SovereignEvolutionEngine:
    """
    Sovereign AGI Otonom Evrim ve İyileştirme Motoru.
    Denetçi (Auditor) tarafından saptanan açıkları otonom olarak giderir.
    """
    def __init__(self):
        self.active_proposals = []
        # Geçmişte başarısız olan veya reddedilen çözümlerin hafızası (Negative Synapses)
        self.negative_synapses = set() 

    async def run_evolution_cycle(self):
        """Standard Evrim döngüsü: Denetle -> Öner -> Doğrula -> Uygula."""
        from libs.config import ENABLE_AUTONOMOUS_IMPROVEMENT, IMPROVEMENT_AUTO_APPLY_THRESHOLD
        
        logger.info(f"[EVOLUTION] Sovereign Evolution: Döngü başlatıldı.")
        
        # [PHASE 52] Specialist Forging: Başarılı desenlerden uzman damıt (Metabolizma)
        try:
            from libs.db.session import async_session
            async with async_session() as db:
                await self.run_specialist_forge_cycle(db)
        except Exception as e:
            logger.warning(f"[EVOLUTION] Specialist Forge hatası: {e}")

        # Auditor Findings
        findings = await sovereign_auditor.run_full_audit()
        if not findings:
            logger.info("[EVOLUTION] İyileştirilecek bir alan bulunamadı.")
            return

        for finding in findings:
            finding_id = finding.get("id")
            if finding_id in self.negative_synapses or any(p["finding"].get("id") == finding_id for p in self.active_proposals):
                continue

            patch = await proposer.propose_fix(finding)
            if not patch: 
                continue
                
            success, confidence, reasoning = await cognitive_verifier.verify_patch(patch, finding)
            if success:
                proposal = {
                    "id": str(uuid.uuid4()), "finding": finding, "patch": patch,
                    "status": "pending_approval", "confidence": confidence,
                    "reasoning": reasoning, "created_at": datetime.now(timezone.utc).isoformat()
                }
                
                if ENABLE_AUTONOMOUS_IMPROVEMENT and confidence >= IMPROVEMENT_AUTO_APPLY_THRESHOLD:
                    await self.apply_evolution(proposal)
                    await self._report_event(proposal, auto=True)
                else:
                    self.active_proposals.append(proposal)
                    await self._report_event(proposal, auto=False)
            else:
                self.negative_synapses.add(finding_id)
                logger.error(f"[EVOLUTION] Yama reddedildi: {finding.get('title')}")


    async def run_specialist_forge_cycle(self, db: AsyncSession):
        """Başarılı desenlerden yeni uzman ajanlar sentezler. (Phase 52)"""
        logger.info("[EVOLUTION] Uzman Sentezi (Specialist Forge) döngüsü başlatıldı.")
        new_specialists = await specialist_forge.forge_new_specialists(db)
        if new_specialists:
            logger.info(f"[EVOLUTION] {len(new_specialists)} yeni uzman ajan sisteme eklendi.")

    # --- PART 2: Policy-Driven Evolution (Integrated from SovereignEvolution45) ---

    async def evolve_from_policies(self, db: AsyncSession):
        """Bekleyen politikaları (Policies) somut kod yamalarına dönüştürür. (v45 Entegrasyonu)"""
        logger.info("[EVOLUTION] Politika bazlı evrim döngüsü başlatıldı (v45).")
        
        stmt = select(Memory).where(Memory.category == "policy_proposal").order_by(Memory.created_at)
        result = await db.execute(stmt)
        memories = [m for m in result.scalars().all() if m.metadata_.get("status") == "pending"]

        if not memories:
            logger.info("[EVOLUTION] Bekleyen politika bulunamadı.")
            return

        from libs.llm.model_orchestrator import ModelOrchestrator
        orch = ModelOrchestrator()

        for m_policy in memories:
            rule = m_policy.metadata_.get("proposed_rule", "")
            reason = m_policy.metadata_.get("reason", "")
            
            prompt = f"POLİTİKA: {rule}\nNEDEN: {reason}\n\nBu kuralı uygulamak için gereken dosyayı ve TAM içerik değişimini JSON dön:\n{{'file_path': '...', 'new_content': '...'}}"
            try:
                response = await orch.complete_task(agent_role="architect", prompt=prompt)
                match = re.search(r'\{.*\}', response.content, re.DOTALL)
                if not match: continue
                
                insight = json.loads(match.group())
                target_file = insight.get("file_path")
                new_code = insight.get("new_content")

                # Güvenlik Denetimi
                if await audit_gate.verify_self_patch(target_file, new_code, reason=rule):
                    orig_content = ""
                    if os.path.exists(target_file):
                        with open(target_file, "r", encoding="utf-8") as f: orig_content = f.read()

                    res = patching_sandbox.apply_atomic_patch(target_file, new_code)
                    if res["success"]:
                        await provenance_engine_45.record_evolution_step(db, target_file, orig_content, new_code, str(m_policy.id), reason)
                        m_policy.metadata_ = {**m_policy.metadata_, "status": "active", "applied_patch": res["backup"]}
                        logger.info(f"[EVOLUTION] Politika başarıyla yamalandı: {target_file}")
                    else:
                        m_policy.metadata_ = {**m_policy.metadata_, "status": "failed", "error": res["error"]}
            except Exception as e:
                logger.error(f"Policy-to-patch failed: {e}")

    # --- PART 3: Recursive Optimization (Integrated from EvolutionaryExecutor) ---

    async def consider_recursive_evolution(self, episode: EpisodeRecord, causal_graph: CausalGraph):
        """Başarısız epizotlar sonrası otonom öz-iyileştirme tetikler. (Executor Entegrasyonu)"""
        if episode.verification and episode.services.repair.verification.result_status:
            return
            
        root_cause = causal_graph.nodes_metadata.get("root_cause_step")
        if not root_cause: return
            
        logger.info(f"[EVOLUTION] Otonom öz-iyileştirme tetiklendi. Kök Neden: {root_cause}")
        
        from libs.llm.model_orchestrator import ModelOrchestrator
        orch = ModelOrchestrator()
        
        prompt = f"HATA KÖK NEDENİ: {root_cause}\nÇözüm için kod iyileştirme planı (JSON) çıkar: {{'target_file': '...', 'proposed_logic': '...'}}"
        try:
            resp = await orch.complete_task(agent_role="architect", prompt=prompt)
            opportunity = json.loads(re.search(r'\{.*\}', resp.content, re.DOTALL).group())
            
            target_file = opportunity.get("target_file")
            if not target_file or not os.path.exists(target_file): return

            with open(target_file, "r", encoding="utf-8") as f: current_code = f.read()
            patch_prompt = f"HEDEF: {target_file}\nKOD:\n{current_code}\n\nİyileştirilmiş kodu üret."
            
            resp_patch = await orch.complete_task(agent_role="backend_dev", prompt=patch_prompt)
            new_code = resp_patch.content

            if await audit_gate.verify_self_patch(target_file, new_code, reason=f"Recursive self-optimization for {root_cause}"):
                res = patching_sandbox.apply_atomic_patch(target_file, new_code)
                if res["success"]:
                    logger.info(f"[EVOLUTION] Rekürsif iyileştirme uygulandı: {target_file}")
        except Exception as e:
            logger.error(f"Recursive evolution failed: {e}")

    async def _report_event(self, proposal: Dict, auto: bool = False):
        """Evrim olaylarını raporlar."""
        try:
            from services.orchestration.agi.cognitive.sovereign_cortex import nexus_orchestrator as orchestrator
            from services.orchestration.agi.cognitive.chronicler import chronicler
            from services.orchestration.agi.consciousness.affective_core import affective_core
            
            msg = f"{'OTONOM ' if auto else ''}Evrim Adımı: {proposal['finding']['title']}"
            await chronicler.record_provenance_structured({
                "action": "EVOLUTION_APPLIED" if auto else "EVOLUTION_PROPOSED",
                "finding_id": proposal["finding"]["id"],
                "reason": proposal["finding"]["description"],
                "confidence": proposal["confidence"],
                "reasoning": proposal["reasoning"],
                "affective_state": affective_core.get_state_matrix()
            })
            
            await event_bus.emit(
                "evolution_report",
                message=msg,
                auto=auto,
                finding_id=proposal["finding"]["id"],
                confidence=proposal["confidence"]
            )
        except Exception as e:
            logger.error(f"Reporting evolution failed: {e}")

    async def apply_evolution(self, proposal: Dict):
        """Onaylanan evrim adımını sisteme uygular."""
        from services.orchestration.agi.cognitive.sovereign_cortex import nexus_orchestrator as orchestrator
        if not orchestrator.self_updater: return

        finding = proposal["finding"]
        patch = proposal["patch"]
        target_file = finding.get("evidence", {}).get("affected_file", "core/orchestrator.py")
        if not target_file.endswith(".py") and "/" not in target_file: target_file = f"api/{target_file}.py"

        logger.info(f"[EVOLUTION] Sistem dosyası güncelleniyor: {target_file}")
        await orchestrator.self_updater.modify_system_file(
            target_file_path=target_file,
            instruction=f"Sovereign Evolution: {patch}"
        )
        matching = [p for p in self.active_proposals if p["id"] == proposal["id"]]
        for m in matching: self.active_proposals.remove(m)

    async def get_active_proposals(self) -> List[Dict]:
        return self.active_proposals

evolution_engine = SovereignEvolutionEngine()

async def start_evolution_loop():
    """Arka planda periyodik evrim taraması yapar."""
    while True:
        try:
            await asyncio.sleep(600)  # 10 dakikada bir çalış
            await evolution_engine.run_evolution_cycle()
        except Exception as e:
            logger.error(f"Evolution loop error: {e}")
            await asyncio.sleep(60)
