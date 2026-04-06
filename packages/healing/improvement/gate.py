"""
Self-Improvement: Gate
İyileştirme süreçlerini yöneten ana merkez (Orchestrator).
"""
import asyncio
from typing import List, Dict
from .observer import observer
from .proposer import proposer
from .verifier import verifier
from packages.observability.logging import get_logger

logger = get_logger("improvement.gate")

class ImprovementGate:
    def __init__(self):
        self.active_proposals = []

    async def run_cycle(self):
        """Kendi kendini iyileştirme döngüsünü başlatır."""
        from config import ENABLE_AUTONOMOUS_IMPROVEMENT, IMPROVEMENT_AUTO_APPLY_THRESHOLD
        logger.info(f"Self-Improvement loop started. Auto-apply: {ENABLE_AUTONOMOUS_IMPROVEMENT}")
        
        # 1. Gözlemle (Problemleri Bul)
        issues = await observer.scan_for_issues()
        if not issues:
            logger.info("No issues found for improvement.")
            return

        for issue in issues:
            # Mükerrer kontrolü
            if any(p["issue"].get("reason") == issue["reason"] for p in self.active_proposals):
                continue

            # 2. Öneri Al
            patch = await proposer.propose_fix(issue)
            if not patch:
                continue
                
            # 3. Doğrula
            success = await verifier.verify_patch(patch, issue)
            
            if success:
                proposal = {
                    "issue": issue,
                    "patch": patch,
                    "status": "pending_approval",
                    "confidence": 0.85 # Mock confidence for now
                }
                
                # Otonom Uygulama Kontrolü
                if ENABLE_AUTONOMOUS_IMPROVEMENT and proposal["confidence"] >= IMPROVEMENT_AUTO_APPLY_THRESHOLD:
                    logger.warning(f"Self-Improvement: Otomatik uygulama başlatılıyor! Sebep: {issue['reason']}")
                    await self.apply_proposal(proposal)
                    await self._report_improvement(proposal, auto=True)
                else:
                    self.active_proposals.append(proposal)
                    logger.warning(f"Self-Improvement: Yeni bir çözüm onay bekliyor! Ajan: {issue['agent_id']}")

    async def _report_improvement(self, proposal: Dict, auto: bool = False):
        """İyileştirme sonucunu kullanıcıya raporlar (WS üzerinden)."""
        from packages.orchestration.agi.cognitive.sovereign_cortex import nexus_orchestrator as orchestrator
        msg = f"{'OTONOM ' if auto else ''}İyileştirme Uygulandı: {proposal['issue']['reason']}"
        if orchestrator.ws_manager:
            await orchestrator.ws_manager.broadcast({
                "event": "improvement_report",
                "severity": "success",
                "message": msg,
                "proposal_id": proposal.get("id", "auto"),
                "auto": auto
            })
        logger.info(f"REPORT: {msg}")

    async def get_proposals(self) -> List[Dict]:
        return self.active_proposals

    async def apply_proposal(self, proposal: Dict):
        """Onaylanan yamayı sisteme uygular."""
        from packages.orchestration.agi.cognitive.sovereign_cortex import nexus_orchestrator as orchestrator
        if not orchestrator.self_updater:
            logger.error("Self-Updater modülü bulunamadı, yama uygulanamıyor.")
            return

        issue = proposal["issue"]
        patch = proposal["patch"]
        
        target_file = issue.get("agent_id", "core/orchestrator.py")
        if not target_file.endswith(".py") and "/" not in target_file:
             target_file = f"agents/{target_file}.py"

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
