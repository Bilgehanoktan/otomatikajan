"""
Self-Improvement: Gate
İyileştirme süreçlerini yöneten ana merkez (Orchestrator).
"""
import asyncio
from typing import List, Dict
from .observer import observer
from .proposer import proposer
from .verifier import verifier
from services.observability.logging import get_logger

logger = get_logger("improvement.gate")

class ImprovementGate:
    def __init__(self):
        self.active_proposals = []

    async def run_cycle(self):
        """Kendi kendini iyileştirme döngüsünü başlatır."""
        from libs.config import ENABLE_AUTONOMOUS_IMPROVEMENT, IMPROVEMENT_AUTO_APPLY_THRESHOLD
        from libs.db.session import AsyncSessionLocal
        from libs.db.models.core_models import ImprovementOpportunity

        logger.info(f"Self-Improvement loop started. Auto-apply: {ENABLE_AUTONOMOUS_IMPROVEMENT}")

        # 1. Gözlemle (Problemleri Bul)
        opportunities = await observer.scan()
        if not opportunities:
            logger.info("No issues found for improvement.")
            return

        async with AsyncSessionLocal() as session:
            for opp in opportunities:
                # Mükerrer kontrolü (DB üzerinden)
                # Not: pattern_hash sayesinde aynı problem tekrar kaydedilmez (unique constraint var core_models'da)
                try:
                    session.add(opp)
                    await session.commit()
                    logger.info(f"New ImprovementOpportunity recorded: {opp.title}")
                except Exception:
                    await session.rollback() # Zaten varsa devam et

                # 2. Öneri Al
                issue_dict = {
                    "reason": opp.description,
                    "affected_files": opp.affected_files,
                    "agent_id": opp.source_ref
                }

                patch = await proposer.propose_fix(issue_dict)
                if not patch:
                    continue

                # 3. DoÄŸrula
                v_result = await verifier.verify_patch(patch, issue_dict)

                # --- Faz 12.1: Otonom Strateji DeÄŸiÅŸimi (Retry Logic) ---
                if v_result.get("reason") == "axiology_retry_suggested":
                    suggestion = v_result["audit"].get("corrective_action", "")
                    logger.warning(f"Axiology strateji deÄŸiÅŸimi Ã¶nerdi: {suggestion}")

                    # Yeni strateji ile tekrar proposal iste (basitleÅŸtirilmiÅŸ: proposer'a ipucu ver)
                    issue_dict["instruction_hint"] = suggestion
                    patch = await proposer.propose_fix(issue_dict)
                    if patch:
                        v_result = await verifier.verify_patch(patch, issue_dict)

                if v_result.get("success"):
                    proposal = {
                        "issue": issue_dict,
                        "patch": patch,
                        "status": "pending_approval",
                        "confidence": 0.85,
                        "audit": v_result.get("audit")
                    }

                    # Otonom Uygulama KontrolÃ¼
                    if ENABLE_AUTONOMOUS_IMPROVEMENT and proposal["confidence"] >= IMPROVEMENT_AUTO_APPLY_THRESHOLD:
                        logger.warning(f"Self-Improvement: Otomatik uygulama baÅŸlatÄ±lÄ±yor! Sebep: {opp.description}")
                        await self.apply_proposal(proposal)
                        await self._report_improvement(proposal, auto=True)
                    else:
                        # Mükerrer teklif kontrolü (RAM listesinde)
                        if not any(p["issue"]["reason"] == opp.description for p in self.active_proposals):
                            self.active_proposals.append(proposal)
                            logger.warning(f"Self-Improvement: Yeni bir çözüm onay bekliyor! Ajan: {opp.source_ref}")

    async def _report_improvement(self, proposal: Dict, auto: bool = False):
        """İyileştirme sonucunu kullanıcıya raporlar (WS üzerinden)."""
        # Report to user via Event Bus
        from services.orchestration.domain.events import event_bus
        msg = f"{'OTONOM ' if auto else ''}İyileştirme Uygulandı: {proposal['issue']['reason']}"
        await event_bus.emit(
            "improvement.report",
            severity="success",
            message=msg,
            proposal_id=proposal.get("id", "auto"),
            auto=auto,
            phase="healing"
        )
        logger.info(f"REPORT: {msg}")

    async def get_proposals(self) -> List[Dict]:
        return self.active_proposals

    async def apply_proposal(self, proposal: Dict):
        """Onaylanan yamayı sisteme uygular."""
        from services.orchestration.agi.cognitive.sovereign_cortex import nexus_orchestrator as orchestrator
        if not orchestrator.self_updater:
            logger.error("Self-Updater modülü bulunamadı, yama uygulanamıyor.")
            return

        issue = proposal["issue"]
        patch = proposal["patch"]

        # Faz 12.1: Hatalı dosya yerine etkilenen dosyayı hedefle
        affected = issue.get("affected_files", [])
        target_file = affected[0] if affected else "core/orchestrator.py"

        logger.info(f"Yama uygulanıyor: {target_file}")

        await orchestrator.self_updater.modify_system_file(
            target_file_path=target_file,
            instruction=f"Apply this optimized fix: {patch}"
        )

        # Uygulananı listeden kaldır
        if proposal in self.active_proposals:
            self.active_proposals.remove(proposal)

improvement_gate = ImprovementGate()

# --- Background Loop ---
async def start_improvement_background_loop():
    while True:
        try:
            await asyncio.sleep(600) # Her 10 dakikada bir çalış
            await improvement_gate.run_cycle()
        except Exception as e:
            logger.error(f"Improvement loop error: {e}")
            await asyncio.sleep(60)
