import asyncio
import time
from typing import List, Dict, Any, Optional
from services.orchestration.agi.governance.rules import GovernanceRules, GovernanceViolation
from services.orchestration.agi.schemas import PlanProposal
from services.repair.application.heal_engine import heal_engine
from services.observability.logging import get_logger

_log = get_logger("agi_governance_watchdog")

class GovernanceWatchdog:
    """
    Sovereign AGI Öz-Denetim Gözlemcisi (Phase 41).
    Sistemi periyodik olarak mimari/politika kural dışı durumlar için tarar.
    Tespit edilenleri RepairOrchestrator üzerinden otonom onarır.
    """
    
    def __init__(self, project_root: str = ".", interval_seconds: int = 60, model_orch = None):
        self.project_root = project_root
        self.interval_seconds = interval_seconds
        self.model_orch = model_orch
        self._running = False
        self._last_audit_score = 1.0 # 0.0 to 1.0
        self._instinct_count = 0 
        self._prevented_count = 0 # Faz 43: Önlenen İhlaller

    async def predict_violations(self, subtasks: List[Any]) -> List[GovernanceViolation]:
        """
        Faz 43: Planlama aşamasında ihlal öngörüsü yapar (Shadow Audit).
        Henüz çalışmamış ajan promplarını tarayarak riskli eylemleri engeller.
        """
        predicted = []
        for st in subtasks:
            # SubTask.prompt içeriğini denetle
            prompt_violations = await GovernanceRules.audit_text_prompt(st.prompt)
            for v in prompt_violations:
                v.agent_id = st.agent_id # İhlali yapan ajanı işaretle
                predicted.append(v)
        
        if predicted:
            self._prevented_count += len(predicted)
            _log.warning(f"[GOVERNANCE-PREDICTION] {len(predicted)} olası ihlal engellendi ve re-planning tetiklendi.")
            
        return predicted

    async def start(self):
        if self._running:
            return
        self._running = True
        _log.info(f"Governance Watchdog AKTİF (Interv: {self.interval_seconds}s)")
        asyncio.create_task(self._run_loop())

    async def stop(self):
        self._running = False
        _log.info("Governance Watchdog durduruluyor...")

    async def _run_loop(self):
        while self._running:
            try:
                await self.audit_and_repair()
            except Exception as e:
                _log.error(f"Watchdog döngü hatası: {e}")
            await asyncio.sleep(self.interval_seconds)

    async def audit_and_repair(self):
        """Sistemi denetler ve gerekirse onarım başlatır."""
        violations = await GovernanceRules.audit_project_structure(self.project_root)
        
        if not violations:
            self._last_audit_score = 1.0
            return

        # Puan hesapla (basit)
        self._last_audit_score = max(0.0, 1.0 - (len(violations) * 0.1))
        _log.warning(f"[GOVERNANCE] {len(violations)} kural ihlali tespit edildi! Sağlık Skoru: {self._last_audit_score:.2f}")

        # Her ihlal için RepairOrchestrator tetikle
        from services.repair.application.orchestrator import get_repair_orchestrator
        orch = get_repair_orchestrator(model_orch=self.model_orch)
        
        from services.repair.schemas.incident import IncidentRecord

        for v in violations:
            _log.info(f"[GOVERNANCE] Otonom onarım başlatılıyor: {v.rule_id} ({v.target})")
            
            # 1. Incident Hazırla
            incident = IncidentRecord(
                incident_id=f"gov_v_{int(time.time())}_{v.rule_id}",
                symptom=v.description,
                module="governance",
                severity="low" if v.severity.value == "low" else "medium",
                stack_trace="",
                context=GovernanceRules.get_repair_payload(v)["context"]
            )
            
            # 2. Onarımı tetikle
            await orch.start_repair(incident)

            # 3. Faz 42: Bilişsel Ketleme (Reinforcement Learning)
            try:
                from services.orchestration.agi.cognitive.synaptic_cortex import synaptic_cortex
                from libs.db.session import get_db, get_db_ctx
                async with get_db_ctx() as db:
                    await synaptic_cortex.save_architectural_inhibition(
                        db=db,
                        rule_id=v.rule_id,
                        target=v.target,
                        description=v.description
                    )
            except Exception as re_err:
                _log.error(f"Reinforcement recording failed: {re_err}")

        # Update instinct count badge
        try:
            from services.orchestration.agi.cognitive.synaptic_cortex import synaptic_cortex
            from libs.db.session import get_db, get_db_ctx
            async with get_db_ctx() as db:
                inhibs = await synaptic_cortex.get_architectural_inhibitions(db, limit=100)
                self._instinct_count = len(inhibs)
        except:
            pass

    @property
    def health_score(self) -> float:
        return self._last_audit_score

    @property
    def instinct_count(self) -> int:
        return self._instinct_count

    @property
    def prevented_count(self) -> int:
        return self._prevented_count

# Singleton / Default instance
governance_watchdog = GovernanceWatchdog()
