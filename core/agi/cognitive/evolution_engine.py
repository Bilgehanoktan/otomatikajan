import asyncio
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from .sovereign_auditor import sovereign_auditor
from core.improvement.proposer import proposer
from core.improvement.cognitive_verifier import cognitive_verifier
from observability.logging import get_logger

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
        """Evrim döngüsünü başlatır: Denetle -> Öner -> Doğrula -> Uygula."""
        from config import ENABLE_AUTONOMOUS_IMPROVEMENT, IMPROVEMENT_AUTO_APPLY_THRESHOLD
        
        logger.info(f"[EVOLUTION] Sovereign Evolution: Döngü başlatıldı. Otonom Mod: {ENABLE_AUTONOMOUS_IMPROVEMENT}")
        
        # 1. Denetle (Göremediğimiz hataları ve gelişim alanlarını bul)
        findings = await sovereign_auditor.run_full_audit()
        if not findings:
            logger.info("[EVOLUTION] Sovereign Evolution: İyileştirilecek bir alan bulunamadı.")
            return

        for finding in findings:
            finding_id = finding.get("id")
            title = finding.get("title")
            
            # Mükerrer veya Negatif Sinaps Kontrolü
            if any(p["finding"].get("id") == finding_id for p in self.active_proposals):
                continue
            if finding_id in self.negative_synapses:
                continue

            # 2. Öner (LLM tabanlı çözüm önerisi üret)
            # Not: Mevcut proposer 'issue' beklediği için finding'i uygun formata sokuyoruz.
            patch = await proposer.propose_fix(finding)
            if not patch:
                logger.debug(f"[EVOLUTION] Sovereign Evolution: '{title}' için yama üretilemedi.")
                continue
                
            # 3. Bilişsel Doğrulama (Reflective Reasoning + Sandbox Simülasyonu)
            success, confidence, reasoning = await cognitive_verifier.verify_patch(patch, finding)
            
            if success:
                proposal = {
                    "id": str(uuid.uuid4()),
                    "finding": finding,
                    "patch": patch,
                    "status": "pending_approval",
                    "confidence": confidence,
                    "reasoning": reasoning,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                
                # Otonom Uygulama Eşiği Kontrolü
                if ENABLE_AUTONOMOUS_IMPROVEMENT and confidence >= IMPROVEMENT_AUTO_APPLY_THRESHOLD:
                    logger.warning(f"[EVOLUTION] Sovereign Evolution: OTONOM EVRİM! Güven: {confidence:.2f} | Bulgu: {title}")
                    await self.apply_evolution(proposal)
                    await self._report_event(proposal, auto=True)
                else:
                    self.active_proposals.append(proposal)
                    logger.info(f"[EVOLUTION] Sovereign Evolution: Öneri onay bekliyor. Güven: {confidence:.2f} | {title}")
                    await self._report_event(proposal, auto=False)
            else:
                # Failure Learning: Reddedilen çözümü belleğe kaydet
                self.negative_synapses.add(finding_id)
                logger.error(f"[EVOLUTION] Sovereign Evolution: Yama reddedildi: {title}. Gerekçe: {reasoning}")

    async def _report_event(self, proposal: Dict, auto: bool = False):
        """Evrim olaylarını WS ve Chronicler üzerinden raporlar."""
        try:
            from core.agi.cognitive.sovereign_cortex import nexus_orchestrator as orchestrator
            from core.agi.cognitive.chronicler import chronicler
            from core.agi.consciousness.affective_core import affective_core
            
            msg = f"{'OTONOM ' if auto else ''}Evrim Adımı: {proposal['finding']['title']} (Güven: {proposal['confidence']:.2f})"
            
            # Duygusal Bağlam (Affective Trace)
            aff_matrix = affective_core.get_state_matrix()
            
            # Provenance Kaydı
            await chronicler.record_provenance_structured({
                "action": "EVOLUTION_APPLIED" if auto else "EVOLUTION_PROPOSED",
                "finding_id": proposal["finding"]["id"],
                "reason": proposal["finding"]["description"],
                "confidence": proposal["confidence"],
                "reasoning": proposal["reasoning"],
                "affective_state": aff_matrix
            })
            
            if orchestrator.ws_manager:
                await orchestrator.ws_manager.broadcast({
                    "event": "evolution_report",
                    "severity": "success" if auto else "info",
                    "message": msg,
                    "proposal": proposal,
                    "auto": auto
                })
        except Exception as e:
            logger.error(f"Reporting evolution failed: {e}")

    async def apply_evolution(self, proposal: Dict):
        """Onaylanan evrim adımını sisteme uygular."""
        from core.agi.cognitive.sovereign_cortex import nexus_orchestrator as orchestrator
        if not orchestrator.self_updater:
            logger.error("Self-Updater modülü bulunamadı.")
            return

        finding = proposal["finding"]
        patch = proposal["patch"]
        
        # Hedef dosya tespiti (Evidence içinden veya varsayılan)
        target_file = finding.get("evidence", {}).get("affected_file", "core/orchestrator.py")
        if not target_file.endswith(".py") and "/" not in target_file:
             target_file = f"api/{target_file}.py"

        logger.info(f"[EVOLUTION] Sovereign Evolution: Sistem dosyası güncelleniyor: {target_file}")
        
        await orchestrator.self_updater.modify_system_file(
            target_file_path=target_file,
            instruction=f"Sovereign Evolution: Birleşik denetim bulgusu doğrultusunda sistemi iyileştir. (Güven: {proposal['confidence']}): {patch}"
        )
        
        # Uygulananı listeden kaldır
        matching = [p for p in self.active_proposals if p["id"] == proposal["id"]]
        for m in matching:
            self.active_proposals.remove(m)

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
