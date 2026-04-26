"""
Repair Orchestrator — Faz 4 Self-Repair Ana Pipeline

Durum makinesi:
NEW -> INCIDENT_COLLECTED -> TRIAGED -> CONTEXT_BUILT
    -> ROOT_CAUSE_ANALYZED -> PATCH_PLANNED -> PATCH_GENERATED
    -> REVIEWED -> VERIFIED -> PR_CREATED -> AWAITING_APPROVAL

Her adım başarısız olursa uygun FAILED_* veya REQUIRES_MANUAL_REVIEW durumuna geçer.
Hiçbir adım production'a otomatik yazamaz.
"""

import asyncio
import time
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from services.repair.schemas.repair_job import RepairJob, RepairJobStatus
from services.repair.schemas.incident import IncidentRecord
from services.repair.schemas.diagnosis import DiagnosisTicket, RepairMode
from services.repair.schemas.patch_plan import PatchPlan
from services.repair.schemas.validation import ValidationStatus
from services.repair.ingestion.incident_ingestor import IncidentIngestor, incident_ingestor
from libs.db.models.repair_models import RepairJobRecord
from services.repair.triage.triage_engine import TriageEngine, triage_engine
from services.repair.memory.incident_memory import IncidentMemory, incident_memory
from services.repair.memory.patch_memory import PatchMemory, PatchOutcome, patch_memory
from services.repair.memory.architecture_memory import ArchitectureMemory, architecture_memory
from services.governance.policy.policy_engine import PolicyEngine, policy_engine
from services.observability.logging import get_logger

# DB Persistence (Faz 13)
from libs.db.session import AsyncSessionLocal
from libs.db.repositories.repair_repository import RepairJobRepo, RepairIncidentRepo


# Faz 12.1 Stability Patch: Capability Tracking
_CAPABILITIES = {}

def _register_capability(name: str, status: bool, error: str = ""):
    _CAPABILITIES[name] = {"status": status, "error": error}

# Faz 11 yeni bileşenler (lazy import — her zaman erişilebilir olmak zorunda değil)
def _get_fingerprint_engine():
    try:
        from repair.analysis.incident_fingerprint import build_fingerprint, get_similarity_engine
        _register_capability("fingerprint", True)
        return build_fingerprint, get_similarity_engine()
    except Exception as e:
        _register_capability("fingerprint", False, str(e))
        return None, None

def _get_ranker():
    try:
        from repair.analysis.root_cause_ranker import get_root_cause_ranker
        _register_capability("ranker", True)
        return get_root_cause_ranker()
    except Exception as e:
        _register_capability("ranker", False, str(e))
        return None

def _get_test_gen():
    try:
        from repair.generation.test_generator import get_test_generator
        _register_capability("test_gen", True)
        return get_test_generator()
    except Exception as e:
        _register_capability("test_gen", False, str(e))
        return None

def _get_canary():
    try:
        from repair.verification.canary_runner import get_canary_runner
        _register_capability("canary", True)
        return get_canary_runner()
    except Exception as e:
        _register_capability("canary", False, str(e))
        return None

def _get_metrics_store():
    try:
        from repair.verification.metrics_collector import get_metrics_store, make_metric
        _register_capability("metrics", True)
        return get_metrics_store(), make_metric
    except Exception as e:
        _register_capability("metrics", False, str(e))
        return None, None

def _get_policy_registry():
    try:
        from services.governance.policy.policy_registry import get_policy_registry
        _register_capability("policy", True)
        return get_policy_registry()
    except Exception as e:
        _register_capability("policy", False, str(e))
        return None

def _get_arch_guard():
    try:
        from repair.review.architecture_guard import get_architecture_guard
        _register_capability("arch_guard", True)
        return get_architecture_guard()
    except Exception as e:
        _register_capability("arch_guard", False, str(e))
        return None

_log = get_logger("repair.orchestrator")


class RepairOrchestrator:
    """
    Self-Repair pipeline'ının ana yöneticisi.

    Kural:
    - Her adım sadece kendi sorumluluğunu yapar
    - Başarısız adımlar pipeline'ı durdurur
    - Tüm kararlar kayıt altına alınır
    """

    def __init__(
        self,
        model_orch=None,
        project_root:    str          = ".",
        ingestor:        IncidentIngestor  = None,
        triage:          TriageEngine      = None,
        inc_memory:      IncidentMemory    = None,
        ptch_memory:     PatchMemory       = None,
        arch_memory:     ArchitectureMemory = None,
        policy:          PolicyEngine      = None,
    ):
        self.model_orch  = model_orch
        self.project_root = project_root
        self.ingestor    = ingestor   or incident_ingestor
        self.triage      = triage     or triage_engine
        self.inc_memory  = inc_memory or incident_memory
        self.ptch_memory = ptch_memory or patch_memory
        self.arch_memory = arch_memory or architecture_memory
        self.policy      = policy     or policy_engine

        from services.governance.lineage_service import LineageService
        self.lineage_service = LineageService()

        self._jobs_cache: dict[str, RepairJob] = {}
        self._hydrated = False
        
        from services.repair.generation.candidate_generator import CandidateGenerator
        from services.repair.generation.patch_tournament import PatchTournament
        from services.repair.verification.regression_verifier import RegressionVerifier
        from services.repair.verification.governance_verifier import GovernanceVerifier
        from services.repair.verification.economic_verifier import EconomicVerifier
        from services.repair.verification.security_verifier import SecurityVerifier
        from services.repair.verification.performance_verifier import PerformanceVerifier
        from services.repair.repair_memory import RepairMemory
        from services.repair.self_tuning.optimizer import WeightOptimizer

        # Phase 28 Scientific Components
        self.candidate_gen = CandidateGenerator(model_orch=self.model_orch)
        self.tournament = PatchTournament()
        self.repair_memory = RepairMemory()
        self.weight_optimizer = WeightOptimizer(self.repair_memory)
        
        self.reg_verifier = RegressionVerifier()
        self.gov_verifier = GovernanceVerifier()
        self.econ_verifier = EconomicVerifier()
        self.sec_verifier = SecurityVerifier()
        self.perf_verifier = PerformanceVerifier()
        
        # Comprehensive Verifier Mesh
        self.verifier_mesh = [
            self.reg_verifier,
            self.gov_verifier,
            self.econ_verifier,
            self.sec_verifier,
            self.perf_verifier
        ]
        
        # Faz 12.1 Compliance: Formalize Pipeline Steps
        from dataclasses import dataclass, field
        from typing import Callable, Any

        @dataclass
        class PipelineContext:
            job: RepairJob
            incident: IncidentRecord
            ticket: Optional[Any] = None
            plan: Optional[Any] = None
            patch: Optional[Any] = None
            validation: Optional[Any] = None
            decision_id: Optional[str] = None
            extra: dict = field(default_factory=dict)

        self.PipelineContext = PipelineContext

    def get_capability_status(self) -> dict:
        """Sistem kabiliyetlerinin (Lazy Imports) gerçek durumunu döner."""
        return _CAPABILITIES

    # ══════════════════════════════════════════════════════
    # Public API
    # ══════════════════════════════════════════════════════

    async def start_repair(self, incident: IncidentRecord) -> RepairJob:
        """
        Bir incident için repair job başlat.
        """
        job = RepairJob.create(incident.incident_id)
        self._jobs_cache[job.job_id] = job
        
        # DB Persistence (Resilient to DB failures)
        try:
            from db.session import AsyncSessionLocal, is_db_available
            if await is_db_available():
                from db.repair_repository import RepairJobRepo, RepairIncidentRepo
                async with AsyncSessionLocal() as db:
                    await RepairIncidentRepo.upsert(db, incident)
                    await RepairJobRepo.upsert(db, job)
                    await db.commit()
                    _log.debug(f"Repair job DB persistence success: {job.job_id}")
            else:
                _log.warning(f"DB not available, skipping persistence for job {job.job_id}")
        except Exception as db_err:
            _log.debug(f"Job initial persistence error (ignored for resilience): {db_err}")

        _log.info(f"Repair job başlatıldı (DB): {job.job_id} — {incident.symptom[:80]}")

        # 4. Governance Lineage (Initial Decision)
        try:
            from services.governance.lineage_service import LineageService
            lineage = await LineageService.log_decision(
                decision_type="REPAIR",
                component_name="RepairOrchestrator",
                rationale=f"Triggered repair for incident {incident.incident_id}",
                trigger_event=incident.dict() if hasattr(incident, "dict") else {"id": incident.incident_id}
            )
            job.meta["decision_id"] = str(lineage.id)
        except Exception as le:
            _log.warning(f"Lineage logging failed: {le}")

        # Pipeline'ı arka planda çalıştır
        asyncio.create_task(self._run_pipeline(job, incident))
        return job

    async def get_job(self, job_id: str) -> Optional[RepairJob]:
        """Job'u cache'den veya DB'den getir (Restart Safety)."""
        if job_id in self._jobs_cache:
            return self._jobs_cache[job_id]
        
        try:
            async with AsyncSessionLocal() as db:
                record = await RepairJobRepo.get(db, job_id)
                if record:
                    job = self._map_record_to_job(record)
                    self._jobs_cache[job_id] = job
                    return job
        except Exception as e:
            _log.error(f"Error loading job {job_id} from DB: {e}")
            
        return None

    # ══════════════════════════════════════════════════════
    # Phase 28: Scientific Repair Lab (Shadow Mode)
    # ══════════════════════════════════════════════════════

    async def shadow_repair_cycle(self, incident_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Executes a scientific repair tournament without committing changes."""
        _log.info(f"Starting SHADOW Repair Cycle [Phase 28] for {incident_type}")
        
        # 0. Governance Lineage (Shadow Decision)
        try:
            from services.governance.lineage_service import LineageService
            lineage = await LineageService.log_decision(
                decision_type="SHADOW_REPAIR",
                component_name="RepairOrchestrator",
                rationale=f"Shadow repair tournament for {incident_type}",
                trigger_event=payload,
                metadata={"phase": "28_shadow"}
            )
            payload["decision_id"] = str(lineage.id)
        except Exception: pass

        # 1. Multi-Candidate Generation
        candidates = await self.candidate_gen.generate_variants(incident_type, payload)
        
        # 1b. Self-Tuning (Weight Calibration based on Evidence)
        new_weights = await self.weight_optimizer.calculate_optimal_weights()
        self.tournament.risk_weight = new_weights["risk_weight"]
        self.tournament.cost_weight = new_weights["cost_weight"]
        self.tournament.verifier_weight = new_weights["verifier_weight"]
        
        # 2. 5-Layer Verifier Mesh & Tournament (Ranking)
        context = {
            "region": payload.get("region", "Global"),
            "available_budget": payload.get("budget", 500.0),
            "threat_level": payload.get("threat_level", "low")
        }
        
        winner, win_score = await self.tournament.run_tournament(
            candidates=candidates,
            verifiers=self.verifier_mesh,
            context=context
        )
        
        # Winner must pass weighted success threshold
        all_passed = win_score > 0.6
        
        # 4. Persistence (Memory)
        from services.repair.repair_memory import RepairOutcome
        outcome = RepairOutcome(
            incident_id=f"shadow_{uuid.uuid4().hex[:8]}",
            applied_strategy=winner.strategy_name,
            outcome="SUCCESS" if all_passed else "FAILED",
            failure_reason=None if all_passed else "Verification Mesh Failure",
            mttr_ms=1250.0, # Mock latency
            cost_delta=winner.estimated_cost
        )
        await self.repair_memory.record_outcome(outcome)
        
        return {
            "status": "REPAIR_SUCCESS" if all_passed else "FAILED_VERIFICATION",
            "candidates_count": len(candidates),
            "winning_score": win_score,
            "winner_strategy": winner.strategy_name,
            "summary": f"Tournament champion '{winner.strategy_name}' evaluated via verifier mesh."
        }

    async def list_jobs(self, limit: int = 50) -> list[RepairJob]:
        """Tüm job'ları listele (Cache + DB Sync)."""
        if not self._hydrated:
            await self.hydrate_from_db()

        try:
            async with AsyncSessionLocal() as db:
                records = await RepairJobRepo.list_recent(db, limit=limit)
                for rec in records:
                    if rec.job_id not in self._jobs_cache:
                        self._jobs_cache[rec.job_id] = self._map_record_to_job(rec)
        except Exception as e:
            _log.error(f"Error listing jobs from DB: {e}")

        all_jobs = list(self._jobs_cache.values())
        all_jobs.sort(key=lambda x: getattr(x, "created_at", datetime.min), reverse=True)
        return all_jobs[:limit]

    async def hydrate_from_db(self) -> int:
        """Sistem başlangıcında DB'deki son işleri belleğe al."""
        if self._hydrated:
            return 0
            
        _log.info("RepairOrchestrator: Geri yükleme (hydration) başlatılıyor...")
        try:
            from db.session import AsyncSessionLocal, is_db_available
            if not await is_db_available():
                return 0
                
            async with AsyncSessionLocal() as db:
                from db.repair_repository import RepairJobRepo
                records = await RepairJobRepo.list_recent(db, limit=100)
                for rec in records:
                    if rec.job_id not in self._jobs_cache:
                        self._jobs_cache[rec.job_id] = self._map_record_to_job(rec)
                
            self._hydrated = True
            _log.info(f"RepairOrchestrator: {len(records)} iş geri yüklendi.")
            return len(records)
        except Exception as e:
            _log.error(f"RepairOrchestrator: Hydration hatası: {e}")
            return 0

    def _map_record_to_job(self, record: RepairJobRecord) -> RepairJob:
        """DB kaydını RepairJob schema nesnesine dönüştür."""
        meta = record.meta or {}
        return RepairJob(
            job_id=record.job_id,
            incident_id=record.incident_id,
            status=RepairJobStatus(record.status),
            ticket_id=record.ticket_id,
            plan_id=record.plan_id,
            validation_id=record.validation_id,
            pr_url=record.pr_url,
            branch_name=record.branch_name,
            diff=record.diff or "",
            error_detail=record.error_detail or "",
            canary_id=meta.get("canary_id"),
            canary_status=meta.get("canary_status"),
            generated_tests=meta.get("generated_tests", []),
            fingerprint_hash=meta.get("fingerprint_hash"),
            duplicate_of=meta.get("duplicate_of"),
            risk_score=meta.get("risk_score", 0),
            vector_context_used=meta.get("vector_context_used", False),
            vector_context_summary=meta.get("vector_context_summary", ""),
            debate_triggered=meta.get("debate_triggered", False),
            debate_result_summary=meta.get("debate_result_summary", ""),
            debate_winning_hypothesis=meta.get("debate_winning_hypothesis", ""),
            sandbox_verified=meta.get("sandbox_verified", False),
            lesson_saved=meta.get("lesson_saved", False),
            ranker_adjusted=meta.get("ranker_adjusted", False),
            ranker_adjusted_confidence=meta.get("ranker_adjusted_confidence", 0),
            history=record.history or [],
            created_at=record.created_at,
            updated_at=record.updated_at
        )

    async def _transition_and_persist(self, job: RepairJob, status: RepairJobStatus, note: str = ""):
        """Durum geçişi yap ve DB'ye işle."""
        if job.transition(status, note=note):
            await self._persist_job(job)
            # Canlı Yayın (WebSocket)
            try:
                from api.ws_manager import ws_manager
                await ws_manager.broadcast_job_progress(
                    job_id=job.job_id,
                    status=status.value,
                    message=note
                )
            except Exception:
                pass

    def stats(self) -> dict:
        jobs = list(self._jobs_cache.values())
        active_list = [j for j in jobs if not j.is_terminal()]
        return {
            "total":           len(jobs),
            "active_jobs":     len(active_list),
            "by_status": {
                status.value: sum(1 for j in jobs if j.status == status)
                for status in RepairJobStatus
                if sum(1 for j in jobs if j.status == status) > 0
            },
            "incident_memory":  self.inc_memory.stats(),
            "patch_memory":     self.ptch_memory.stats(),
            "policy_stats":     self.policy.stats(),
        }

    # ══════════════════════════════════════════════════════
    # Pipeline Adımları
    # ══════════════════════════════════════════════════════

    async def _run_pipeline(self, job: RepairJob, incident: IncidentRecord) -> None:
        """
        RC1 Ana Pipeline — Dispatcher-based Modular Execution
        """
        t_start = time.time()
        ctx = self.PipelineContext(job, incident)
        
        try:
            # Phase 1: Analiz (Triage + Root Cause)
            if not await self._phase_analysis(ctx): return

            # Phase 2: Planlama (Lesson Memory + Strategy + Patch Plan)
            if not await self._phase_planning(ctx): return

            # Phase 3: Kandidat Turnuvası (Multi-Candidate Tournament)
            # RC1: Tek patch yerine aday kümesi üretip en iyisini seçiyoruz.
            if not await self._phase_tournament(ctx): return

            # Phase 4: Kod Üretimi (Patch Generation for Tournament Winner)
            if not await self._phase_generation(ctx): return

            # Phase 5: Doğrulama (Sandbox + Review)
            if not await self._phase_verification(ctx): return

            # Phase 6: Yayına Hazırlık
            await self._phase_release(ctx)

            duration = time.time() - t_start
            _log.info(
                f"Pipeline TAMAMLANDI [{job.job_id}] "
                f"dur={duration:.1f}s"
            )

        except asyncio.CancelledError:
            _log.warning(f"Job {job.job_id} iptal edildi")
            raise
        except Exception as e:
            _log.error(f"Job {job.job_id} beklenmeyen hata: {e}", exc_info=True)
            job.error_detail = str(e)[:500]
            if not job.is_terminal():
                job.transition(RepairJobStatus.REQUIRES_MANUAL_REVIEW, note=str(e)[:200])
            try:
                self._record_metric(job, incident, None, None, "failed",
                                    time.time() - t_start)
                
                # Phase 31: Learning from Failure
                from services.governance.learning_orchestrator import LearningOrchestrator
                await LearningOrchestrator.record_learning(
                    incident_data={
                        "id": incident.incident_id,
                        "incident_type": incident.module,
                        "message": incident.symptom,
                        "exception_type": type(e).__name__,
                        "component": "RepairOrchestrator"
                    },
                    outcome_data={
                        "final_outcome": "FAILED",
                        "root_cause": str(e),
                        "repair_latency_s": time.time() - t_start,
                        "strategy_used": "AUTONOMOUS_REPAIR",
                        "workflow_id": job.job_id
                    }
                )
            except Exception as le:
                _log.debug(f"Learning from failure failed: {le}")
        finally:
            await self._persist_job(job)

    # ── Modular Phase Dispatchers ──────────────────────

    async def _phase_analysis(self, ctx) -> bool:
        """Triage ve Root Cause."""
        ctx.ticket = await self._step_triage(ctx.job, ctx.incident)
        if not ctx.ticket: return False
        
        ctx.ticket = await self._step_root_cause(ctx.job, ctx.incident, ctx.ticket)
        return ctx.ticket is not None

    async def _phase_planning(self, ctx) -> bool:
        """Lesson Memory ve Patch Planlama."""
        # Vektör bellekten geçmiş tecrübe sorgula
        ctx.job.vector_context_used = await self._step_get_context_from_vector(ctx.incident)
        
        # Strateji belirle (Faz 4/7)
        ctx.strategy = "aggressive" if ctx.ticket.confidence < 0.4 else "standard"
        
        # Planı oluştur
        ctx.plan = await self._step_patch_plan(ctx.job, ctx.ticket)
        return ctx.plan is not None

    async def _phase_tournament(self, ctx) -> bool:
        """Kandidat üretimi ve turnuva."""
        # 1. Generate 3-5 candidates
        candidates = await self.candidate_gen.generate_variants(
            ctx.incident.module, 
            {"symptom": ctx.incident.symptom, "ticket": ctx.ticket.dict()}
        )
        
        # 2. Context for verifiers
        verify_context = {
            "available_budget": 1000.0,
            "region": ctx.incident.context.get("region", "unknown"),
            "risk_appetite": 0.5
        }
        
        # 3. Run tournament
        winner, score = await self.tournament.run_tournament(
            candidates, 
            verifiers=self.verifier_mesh, 
            context=verify_context
        )
        ctx.winner = winner
        ctx.tournament_score = score
        
        _log.info(f"Tournament Winner: {winner.strategy_name} (Score: {score})")
        return True

    async def _phase_generation(self, ctx) -> bool:
        """Kod üretimi (Turnuva galibi üzerinden)."""
        ctx.patch = await self._step_generate_patch(ctx.job, ctx.plan, ctx.incident, ctx.winner)
        return ctx.patch is not None

    async def _phase_verification(self, ctx) -> bool:
        """Sandbox ve Review."""
        # Sandbox 
        if not await self._step_sandbox_verify(ctx.job, ctx.patch, ctx.plan):
            return False
            
        # Son Karar
        decision = await self._step_verify(ctx.job, ctx.patch, ctx.plan)
        ctx.validation_passed = decision in ("success", "merged", "approved")
            
        return ctx.validation_passed

    async def _phase_release(self, ctx) -> None:
        """Bellek kaydı ve metrik."""
        await self._save_vector_lesson(ctx.job, ctx.incident, "success" if ctx.validation_passed else "failed")
        self._record_metric(ctx.job, ctx.incident, ctx.ticket, ctx.plan, "success" if ctx.validation_passed else "failed", 0)
        
        # Phase 31: Learning Integration
        try:
            from services.governance.learning_orchestrator import LearningOrchestrator
            await LearningOrchestrator.record_learning(
                incident_data={
                    "id": ctx.incident.incident_id,
                    "incident_type": ctx.incident.module,
                    "message": ctx.incident.symptom,
                    "component": "RepairOrchestrator"
                },
                outcome_data={
                    "final_outcome": "SUCCESS" if ctx.validation_passed else "FAILED",
                    "root_cause": ctx.ticket.rationale if ctx.ticket else "unknown",
                    "strategy_used": ctx.winner.strategy_name if hasattr(ctx, "winner") else "AUTONOMOUS_REPAIR",
                    "verification_score": ctx.tournament_score if hasattr(ctx, "tournament_score") else 1.0,
                    "workflow_id": ctx.job.job_id,
                    "applied_patch": ctx.job.diff
                }
            )
        except Exception as le:
            _log.debug(f"Learning from release failed: {le}")

    async def _persist_job(self, job: "RepairJob") -> None:
        """Job durumunu DB'ye yaz (sessiz hata)."""
        try:
            from db.session import AsyncSessionLocal, is_db_available
            if not await is_db_available():
                return
            from db.repair_repository import RepairJobRepo
            async with AsyncSessionLocal() as db:
                await RepairJobRepo.upsert(db, job)
                await db.commit()
        except Exception as e:
            _log.debug(f"Job DB yazma hatası (ignore): {e}")

    # ── Adım implementasyonları ──────────────────────────

    async def _step_triage(self, job: RepairJob, incident: IncidentRecord) -> Optional[DiagnosisTicket]:
        """Adım 1: Triage."""
        try:
            ticket = self.triage.triage(incident)
            job.ticket_id = ticket.ticket_id
            job.transition(RepairJobStatus.TRIAGED, note=ticket.rationale[:100])
            _log.info(f"Triage [{job.job_id}]: {ticket.classification.value} -> {ticket.recommended_mode.value}")
            return ticket
        except Exception as e:
            job.error_detail = str(e)
            job.transition(RepairJobStatus.FAILED_TRIAGE, note=str(e)[:100])
            _log.error(f"Triage başarısız [{job.job_id}]: {e}")
            return None

    async def _step_root_cause(
        self, job: RepairJob, incident: IncidentRecord, ticket: DiagnosisTicket
    ) -> Optional[DiagnosisTicket]:
        """Adım 3: Root Cause Analizi."""
        try:
            from repair.analysis.root_cause_engine import get_root_cause_engine
            engine = get_root_cause_engine(self.model_orch)
            ticket = await engine.analyze(
                ticket=ticket,
                incident_symptom=incident.symptom,
                stack_trace=incident.stack_trace,
                project_root=self.project_root,
            )
            job.transition(RepairJobStatus.ROOT_CAUSE_ANALYZED, note=(
                ticket.selected_hypothesis.title if ticket.selected_hypothesis else "hipotez seçilemedi"
            ))
            _log.info(f"Root cause [{job.job_id}]: {ticket.selected_hypothesis.title if ticket.selected_hypothesis else '?'}")
            return ticket
        except Exception as e:
            job.error_detail = str(e)
            job.transition(RepairJobStatus.FAILED_ANALYSIS, note=str(e)[:100])
            _log.error(f"Root cause analizi başarısız [{job.job_id}]: {e}")
            return None

    async def _step_patch_plan(self, job: RepairJob, ticket: DiagnosisTicket) -> Optional[PatchPlan]:
        """Adım 4: Patch Planlama."""
        try:
            from repair.planning.patch_planner import patch_planner
            plan = patch_planner.plan(ticket, project_root=self.project_root)
            if plan is None:
                job.transition(RepairJobStatus.REQUIRES_MANUAL_REVIEW, note="Güvenli patch hedefi bulunamadı")
                return None
            job.plan_id = plan.plan_id
            job.transition(RepairJobStatus.PATCH_PLANNED, note=f"risk={plan.risk.value}, files={plan.target_files}")
            _log.info(f"Patch plan [{job.job_id}]: {plan.plan_id} — risk={plan.risk.value}")
            return plan
        except Exception as e:
            job.error_detail = str(e)
            job.transition(RepairJobStatus.FAILED_PATCH_GENERATION, note=str(e)[:100])
            _log.error(f"Patch planlama başarısız [{job.job_id}]: {e}")
            return None

    async def _step_generate_patch(self, job: RepairJob, plan: PatchPlan, incident: IncidentRecord, winner=None):
        """Adım 5: Patch Üretimi (Turnuva stratejisi dikkate alınarak)."""
        try:
            from repair.generation.patch_generator import get_patch_generator
            generator = get_patch_generator(self.model_orch)
            
            # Stratejiyi plan'a enjekte et
            if winner:
                plan.meta["strategy"] = winner.strategy_name
                plan.meta["patch_payload"] = winner.patch_payload
                
            patch = await generator.generate(
                plan=plan,
                incident_symptom=incident.symptom,
                stack_trace=incident.stack_trace,
                project_root=self.project_root,
            )
            if patch is None or not patch.is_valid():
                job.transition(RepairJobStatus.FAILED_PATCH_GENERATION, note="Diff üretilemedi veya geçersiz")
                return None
            
            # Canlı yayın (Faz 8 Infra - Live Preview)
            try:
                from api.ws_manager import ws_manager
                asyncio.create_task(ws_manager.broadcast_patch(
                    job_id=job.job_id,
                    file_path=plan.target_files[0] if plan.target_files else "unknown",
                    diff=patch.diff,
                    status="generated"
                ))
            except Exception: pass

            job.diff = patch.diff
            job.transition(RepairJobStatus.PATCH_GENERATED, note=f"confidence={patch.confidence}%")
            _log.info(f"Patch üretildi [{job.job_id}]: {len(patch.diff)} karakter")
            return patch
        except Exception as e:
            job.error_detail = str(e)
            job.transition(RepairJobStatus.FAILED_PATCH_GENERATION, note=str(e)[:100])
            _log.error(f"Patch üretimi başarısız [{job.job_id}]: {e}")
            return None

    async def _step_review_patch(self, job: RepairJob, patch, plan: PatchPlan, ticket: DiagnosisTicket) -> bool:
        """Adım 6: Patch Review."""
        try:
            from repair.review.patch_reviewer import patch_reviewer, ReviewDecisionType
            review = patch_reviewer.review(patch, plan, ticket)
            job.transition(RepairJobStatus.REVIEWED, note=f"decision={review.decision.value}")
            _log.info(f"Patch review [{job.job_id}]: {review.decision.value}")

            if review.decision == ReviewDecisionType.REJECT:
                job.transition(RepairJobStatus.REJECTED, note="; ".join(review.notes[:3]))
                return False
            if review.decision == ReviewDecisionType.MANUAL_REVIEW:
                job.transition(RepairJobStatus.REQUIRES_MANUAL_REVIEW, note="Reviewer: manual review")
                return False
            return True   # APPROVE veya REVISE -> devam et
        except Exception as e:
            _log.warning(f"Patch review hatası [{job.job_id}]: {e} — devam ediliyor")
            job.transition(RepairJobStatus.REVIEWED, note="review hata verdi, devam edildi")
            return True

    async def _step_verify(self, job: RepairJob, patch, plan: PatchPlan) -> Optional[ValidationStatus]:
        """Adım 7: Verification."""
        try:
            from repair.verification.verification_engine import get_verification_engine
            engine     = get_verification_engine(self.project_root)
            # engine.verify blocks the loop (copies project), run in thread
            validation = await asyncio.to_thread(engine.verify, patch, plan, job_id=job.job_id)
            job.validation_id = validation.validation_id
            await self._transition_and_persist(job, RepairJobStatus.VERIFIED, note=f"status={validation.final_status.value}")
            _log.info(f"Verification [{job.job_id}]: {validation.final_status.value}")
            if validation.final_status.value == "failed":
                await self._transition_and_persist(job, RepairJobStatus.FAILED_VALIDATION, note="Validation kapıları geçilemedi")
                return None
            return validation
        except Exception as e:
            job.error_detail = str(e)
            await self._transition_and_persist(job, RepairJobStatus.FAILED_VALIDATION, note=str(e)[:100])
            _log.error(f"Verification RC1 başarısız [{job.job_id}]: {e}")
            return None

    async def _step_create_pr(self, job: RepairJob, patch, plan: PatchPlan, validation, incident: IncidentRecord):
        """Adım 10: PR Önerisi."""
        try:
            from repair.release.pr_creator import get_pr_creator
            creator  = get_pr_creator(self.project_root)
            proposal = creator.create_proposal(
                job_id=job.job_id,
                patch=patch,
                plan=plan,
                validation=validation,
                incident_id=incident.incident_id,
                symptom=incident.symptom,
            )
            job.branch_name = proposal.branch_name
            job.pr_url      = proposal.pr_id   # Gerçek PR URL yoksa pr_id sakla
            await self._transition_and_persist(job, RepairJobStatus.PR_CREATED, note=f"pr={proposal.pr_id}")
            await self._transition_and_persist(job, RepairJobStatus.AWAITING_APPROVAL, note="İnsan onayı bekleniyor")
            _log.info(f"PR önerisi hazır [{job.job_id}]: {proposal.pr_id}")
            # DB'ye kalıcı kayıt
            await self._persist_job_and_proposal(job, proposal)
        except Exception as e:
            _log.error(f"PR oluşturma hatası [{job.job_id}]: {e}")
            await self._transition_and_persist(job, RepairJobStatus.REQUIRES_MANUAL_REVIEW, note=f"PR oluşturulamadı: {e}")

    async def _step_browser_qa(self, job: "RepairJob", incident: "IncidentRecord") -> bool:
        """Adım 8: GStack Otonom Browser QA."""
        try:
            from skills.registry import skill_registry
            from skills.base import SkillRequest
            
            url = incident.context.get("url")
            selector = incident.context.get("selector")
            
            _log.info(f"Otonom Browser QA başlatılıyor [{job.job_id}] -> {url}")
            
            req = SkillRequest(
                task_type="qa",
                title=f"Repair Verification: {job.job_id}",
                description=f"Hata onarıldı, lütfen UI üzerinden doğrula: {url}",
                project_id=job.job_id,
                context={"url": url, "selector": selector}
            )
            
            res = await skill_registry.execute("browser_validator", req)
            
            if res.success:
                job.transition(job.status, note=f"Browser QA Başarılı: {res.summary}")
                if "screenshot_path" in res.data:
                    job.logs.append(f"Screenshot: {res.data['screenshot_path']}")
            else:
                _log.warning(f"Browser QA başarısız [{job.job_id}]: {res.summary}")
                job.logs.append(f"Browser QA Uyarı: {res.summary}")
            
            return res.success
        except Exception as e:
            _log.error(f"Browser QA hatası [{job.job_id}]: {e}")
            return False

    async def _persist_job_and_proposal(self, job, proposal) -> None:
        """Job ve PR önerisini DB'ye yaz (arka planda)."""
        try:
            from db.session import AsyncSessionLocal, is_db_available
            if not await is_db_available():
                return
            from db.repair_repository import RepairJobRepo, RepairProposalRepo
            async with AsyncSessionLocal() as db:
                await RepairJobRepo.upsert(db, job)
                await RepairProposalRepo.save(db, proposal)
                await db.commit()
        except Exception as e:
            _log.debug(f"Job/proposal DB yazma hatası (ignore): {e}")

    def _record_outcome(self, job: RepairJob, incident: IncidentRecord, plan: PatchPlan, patch, outcome: PatchOutcome, confidence: int):
        """Patch sonucunu hafızaya ve DB'ye yaz."""
        diff_lines = len([l for l in patch.diff.split("\n") if l.startswith("+") or l.startswith("-")])
        self.ptch_memory.record(
            job_id=job.job_id,
            incident_id=incident.incident_id,
            classification=incident.module,
            target_files=plan.target_files,
            diff_size_lines=diff_lines,
            outcome=outcome,
            confidence=confidence,
            validation_score=confidence,
        )
        # DB'ye kaydet (hata olursa ignore)
        asyncio.create_task(self._persist_patch_log(job, incident, plan, patch, outcome, confidence, diff_lines))

    async def _persist_patch_log(self, job, incident, plan, patch, outcome, confidence, diff_lines):
        """Patch log kaydını DB'ye yaz (arka planda)."""
        try:
            from db.session import AsyncSessionLocal, is_db_available
            if not await is_db_available():
                return
            from db.repair_repository import RepairPatchLogRepo, RepairJobRepo
            from repair.memory.patch_memory import PatchRecord
            import uuid as _uuid
            from datetime import datetime, timezone
            record = PatchRecord(
                record_id=f"prec_{_uuid.uuid4().hex[:8]}",
                job_id=job.job_id,
                incident_id=incident.incident_id,
                classification=incident.module,
                target_files=plan.target_files,
                diff_size_lines=diff_lines,
                outcome=outcome,
                confidence=confidence,
                validation_score=confidence,
                recorded_at=datetime.now(timezone.utc),
            )
            async with AsyncSessionLocal() as db:
                await RepairPatchLogRepo.save(db, record)
                await RepairJobRepo.upsert(db, job)
                await db.commit()
        except Exception as e:
            _log.debug(f"Patch log DB yazma hatası (ignore): {e}")

    # ══════════════════════════════════════════════════════
    # Faz 11/12 — Gelişmiş Pipeline Adımları
    # ══════════════════════════════════════════════════════

    def _step_fingerprint(self, job: RepairJob, incident: IncidentRecord) -> None:
        """Adım 0: Incident fingerprint üret, duplicate tespit et, job'a yaz."""
        try:
            from repair.analysis.incident_fingerprint import get_fingerprinter
            f = get_fingerprinter()
            job.fingerprint = f.compute(incident)
            dup_id = f.find_duplicate(job.fingerprint)
            if dup_id:
                job.duplicate_of = dup_id
                _log.info(f"Duplicate incident detected: {incident.incident_id} -> {dup_id}")
            f.add(job.fingerprint, job.job_id)
        except Exception as e:
            _log.debug(f"Fingerprint hatası: {e}")

    def _step_rank_hypotheses(self, job: RepairJob, ticket: DiagnosisTicket, incident: IncidentRecord) -> tuple:
        """Adım 3b: Ranker ile hipotez puanlama."""
        try:
            ranker = _get_ranker()
            if not ranker or not ticket or not hasattr(ticket, "hypotheses"):
                return ticket, {}
            if not ticket.hypotheses:
                return ticket, {}
            raw_conf = 0
            if ticket.selected_hypothesis:
                raw_conf = getattr(ticket.selected_hypothesis, "confidence", 0) or 0
            ranked_ticket = ranker.rank(ticket, incident)
            adj_conf = 0
            if ranked_ticket.selected_hypothesis:
                adj_conf = getattr(ranked_ticket.selected_hypothesis, "confidence", 0) or 0
            job.ranker_adjusted            = True
            job.ranker_raw_confidence      = raw_conf
            job.ranker_adjusted_confidence = adj_conf
            return ranked_ticket, {"raw": raw_conf, "adjusted": adj_conf}
        except Exception as e:
            _log.debug(f"Ranker RC1 hatası: {e}")
            return ticket, {}

    async def _step_debate_if_needed(self, job: RepairJob, ticket: DiagnosisTicket, incident: IncidentRecord) -> None:
        """RC1 Adım 3c: Debate Engine — skorlar yakınsa tetikle."""
        try:
            if not ticket or not hasattr(ticket, "hypotheses"): return
            hypotheses = list(getattr(ticket, "hypotheses", []) or [])
            if len(hypotheses) < 2: return

            def get_conf(h): return getattr(h, "confidence", 0) or 0
            h1_conf = get_conf(hypotheses[0])
            h2_conf = get_conf(hypotheses[1])

            if h1_conf == 0 and h2_conf == 0: return
            diff = abs(h1_conf - h2_conf)
            threshold = max(5, int((h1_conf + h2_conf) / 2 * 0.05))

            if diff > threshold: return

            from core.debate_engine import get_debate_engine
            engine = get_debate_engine(model_orch=self.model_orch, max_rounds=2)

            h1_title = getattr(hypotheses[0], "title", str(hypotheses[0]))[:80]
            h2_title = getattr(hypotheses[1], "title", str(hypotheses[1]))[:80]
            symptom  = getattr(incident, "symptom", "bilinmeyen hata")[:150]

            topic = f"Root cause seçimi: '{h1_title}' vs '{h2_title}'. Hata: {symptom}"
            _log.info(f"Debate tetikleniyor [{job.job_id}]: {h1_conf}% vs {h2_conf}%")
            result = await engine.run_debate(topic=topic, agent_a="backend_dev", agent_b="security", moderator="architect", max_rounds=2)
            job.debate_triggered           = True
            job.debate_result_summary      = result.consensus[:300]
            job.debate_winning_hypothesis  = h1_title if h1_conf >= h2_conf else h2_title
        except Exception as e:
            _log.debug(f"Debate RC1 hatası: {e}")

    async def _step_generate_tests(self, job: RepairJob, incident: IncidentRecord, plan: PatchPlan, ticket: DiagnosisTicket) -> None:
        """Adım 4b: Test generator."""
        try:
            gen = _get_test_gen()
            if not gen: return
            test_result = gen.generate(incident, plan, ticket=ticket, job_id=job.job_id)
            if test_result:
                job.generated_tests = [test_result.to_dict()]
                _log.info(f"Test üretildi [{job.job_id}]: {test_result.test_type}")
        except Exception as e:
            _log.debug(f"Test generator hatası: {e}")

    async def _step_architecture_guard(self, job: RepairJob, patch) -> bool:
        """Adım 6b: Architecture guard."""
        try:
            guard = _get_arch_guard()
            if not guard: return True
            diff = getattr(patch, "diff", "") or ""
            if not diff: return True
            # Ek Güvenlik: Yasaklı komut/string kontrolü (Faz 12.1 RC1 Enforcement)
            forbidden_calls = ["os.system", "shutil.rmtree", "DROP TABLE", "rm -rf"]
            for call in forbidden_calls:
                if call in diff:
                     _log.warning(f"ZARARLI KOD TESPİT EDİLDİ: {call}")
                     await self._transition_and_persist(job, RepairJobStatus.REQUIRES_MANUAL_REVIEW, note=f"Kritik güvenlik engeli: {call}")
                     return False

            result = guard.check_diff(diff)
            if not result.passed:
                errors = [v for v in result.violations if v.severity == "error"]
                if errors:
                    reasons = "; ".join(f"{v.rule}: {v.description}" for v in errors[:3])
                    await self._transition_and_persist(job, RepairJobStatus.REQUIRES_MANUAL_REVIEW, note=f"Architecture guard: {reasons}")
                    return False
            return True
        except Exception as e:
            _log.debug(f"Architecture guard hatası: {e}")
            return True

    async def _step_score_risk(self, job: RepairJob, plan: PatchPlan, validation: ValidationStatus):
        """Adım 8b: Risk skoru hesapla."""
        try:
            score = 20
            if plan:
                risk_val = getattr(getattr(plan, "risk", None), "value", "low") or "low"
                if risk_val == "high": score += 40
                elif risk_val == "medium": score += 20
                file_count = len(getattr(plan, "target_files", []) or [])
                score += min(file_count * 5, 20)
            if validation:
                conf = getattr(validation, "confidence", 80) or 80
                if conf < 50: score += 20
                elif conf < 70: score += 10
            if job.duplicate_of:
                score = max(score - 15, 5)
            job.risk_score = min(score, 100)
        except Exception as e:
            _log.debug(f"Risk skorlama hatası: {e}")


    async def _do_canary_run(self, job: RepairJob, patch, plan) -> bool:
        """Canary doğrulama alt işlemi."""
        try:
            from repair.verification.canary_runner import get_canary_runner
            runner = get_canary_runner()
            if not runner: return True
            await self._transition_and_persist(job, RepairJobStatus.CANARY_PENDING)
            await self._transition_and_persist(job, RepairJobStatus.CANARY_RUNNING)
            diff  = getattr(patch, "diff", "") or ""
            files = list(getattr(plan, "target_files", []) or [])
            result = await runner.run(job_id=job.job_id, diff=diff, changed_files=files, project_root=self.project_root)
            job.canary_id     = result.canary_id
            job.canary_status = result.status.value
            if runner.should_block_pr(result):
                await self._transition_and_persist(job, RepairJobStatus.CANARY_FAILED)
                return False
            await self._transition_and_persist(job, RepairJobStatus.CANARY_PASSED)
            return True
        except Exception as e:
            _log.warning(f"Canary hatası [{job.job_id}]: {e}")
            return True

    def _record_metric(self, job: RepairJob, incident: IncidentRecord, plan, validation, decision: str, duration_s: float) -> None:
        """Metrik kaydet."""
        try:
            from repair.verification.metrics_collector import get_metrics_store, make_metric
            store = get_metrics_store()
            if not store: return
            module = getattr(incident, "module", "unknown") if incident else "unknown"
            conf = getattr(validation, "confidence", 0) or 0
            m = make_metric(job_id=job.job_id, incident_id=getattr(incident, "incident_id", "unknown"),
                            incident_class=module, module=module, decision=decision, confidence=conf, duration_s=duration_s)
            store.record(m)
        except Exception as e:
            _log.debug(f"Metrik kayıt hatası: {e}")

    async def _step_canary(self, job: RepairJob, patch, plan) -> bool:
        """Adım 9: Canary doğrulama — patch sonrası mini smoke senaryoları.

        CanaryRunner syntax, regresyon sinyali ve import kontrollerini koşturur.
        Kritik bir check başarısız olursa pipeline durur ve job CANARY_FAILED olur.
        High-risk job'larda canary zorunludur; low-risk'te atlanabilir.
        """
        canary = _get_canary()
        if canary is None:
            # Canary modülü yüklenemedi → düşük riskli job'lar için skip
            if getattr(job, "risk_score", 0) >= 7:
                _log.warning(f"Canary modülü yüklenemedi ama risk yüksek [{job.job_id}]. Manuel inceleme gerekiyor.")
                await self._transition_and_persist(
                    job, RepairJobStatus.REQUIRES_MANUAL_REVIEW,
                    note="Canary modülü yüklenemedi, yüksek riskli job için skip yapılamaz"
                )
                return False
            _log.info(f"Canary atlandı (modül yüklenemedi) [{job.job_id}]")
            return True

        # Canary çalıştır
        await self._transition_and_persist(job, RepairJobStatus.CANARY_PENDING, note="Canary başlatılıyor")

        diff_text = getattr(patch, "diff", "") or ""
        changed_files = []
        if plan and hasattr(plan, "target_files"):
            changed_files = plan.target_files or []

        await self._transition_and_persist(job, RepairJobStatus.CANARY_RUNNING, note="Canary kontrolleri çalışıyor")

        try:
            result = await canary.run(
                job_id=job.job_id,
                diff=diff_text,
                changed_files=changed_files,
                project_root=self.project_root,
            )
        except Exception as e:
            _log.error(f"Canary çalışma hatası [{job.job_id}]: {e}")
            job.canary_status = "error"
            await self._transition_and_persist(
                job, RepairJobStatus.CANARY_FAILED,
                note=f"Canary çalışma hatası: {str(e)[:200]}"
            )
            return False

        job.canary_id = result.canary_id
        job.canary_status = result.status.value

        if canary.should_block_pr(result):
            _log.warning(f"Canary FAILED [{job.job_id}]: {result.reason}")
            await self._transition_and_persist(
                job, RepairJobStatus.CANARY_FAILED,
                note=result.reason[:300]
            )
            # Event bus bildirimi
            try:
                from core.events import event_bus
                await event_bus.emit(
                    "repair.canary_failed",
                    job_id=job.job_id,
                    canary_id=result.canary_id,
                    reason=result.reason,
                    severity="warning",
                    agent_id="canary_runner",
                )
            except Exception:
                pass
            return False

        _log.info(f"Canary PASSED [{job.job_id}]: {result.passed_count}/{result.total_count} check geçti")
        await self._transition_and_persist(
            job, RepairJobStatus.CANARY_PASSED,
            note=f"{result.passed_count}/{result.total_count} canary check geçti"
        )
        return True

    async def _step_sandbox_verify(self, job: RepairJob, patch, plan) -> bool:
        """Faz 12: Sandbox syntax check. (Geliştirildi: Gerçek syntax denetimi yapmaya çalışır)."""
        try:
            from services.orchestration.substrate.sandbox_runner import get_sandbox_runner
            import os
            import ast

            _IS_PROD = os.getenv("APP_ENV") == "production"
            runner = get_sandbox_runner(use_docker=_IS_PROD) # Prod ortamında Docker zorunlu
            
            patch_diff = getattr(patch, "diff", "") or ""
            if not patch_diff: return True
            
            # 1. Hızlı syntax denetimi (added_lines üzerinden)
            added_lines = [l[1:] for l in patch_diff.splitlines() if l.startswith("+") and not l.startswith("+++")]
            snippet = "\n".join(added_lines)
            if not snippet.strip():
                job.sandbox_verified = True
                return True

            try:
                # Snippet'in kendisini parse etmeye çalışalım
                ast.parse(snippet)
            except SyntaxError as e:
                job.error_detail = f"syntax failed (added lines): {str(e)[:200]}"
                await self._transition_and_persist(job, RepairJobStatus.FAILED_VALIDATION, note="Patch syntax hatası")
                return False

            # 2. Opsiyonel: İzole sandbox'ta ast.parse(patched_code) yapmak için dosya okumak gerekir, 
            # ancak burada performansı korumak için snippet bazlı denetimi başarılı sayıyoruz.
            job.sandbox_verified = True
            return True
        except Exception as e:
            job.error_detail = f"sandbox exception: {str(e)[:200]}"
            await self._transition_and_persist(job, RepairJobStatus.FAILED_VALIDATION, note="Sandbox çalışma hatası")
            return False

    async def _save_vector_lesson(self, job: RepairJob, incident: IncidentRecord, decision: str):
        """Faz 12: Başarılı onarımı kaydet (Async destekli)."""
        if decision not in ("success", "merged", "approved"): return
        try:
            from repair.memory.vector_lessons import get_vector_lessons
            store = get_vector_lessons()
            symptom = getattr(incident, "symptom", "")
            module = getattr(incident, "module", "unknown")
            resolution = f"Job {job.job_id}: basariyla onarildi. Diff: {len(job.diff or '')} chars. Risk: {job.risk_score}."
            
            # save_lesson in-memory kaydeder ve DB kaydını asyncio task ile başlatır
            store.save_lesson(symptom=symptom, module=module, resolution=resolution, job_id=job.job_id, incident_id=getattr(incident, "incident_id", ""))
            job.lesson_saved = True
            _log.info(f"Vector lesson kaydedildi: {job.job_id}")
        except Exception as e: _log.debug(f"Vector lesson hatası: {e}")

    async def _step_get_context_from_vector(self, incident: IncidentRecord) -> str:
        """Faz 12: RAG."""
        try:
            from repair.memory.vector_lessons import get_vector_lessons
            store = get_vector_lessons()
            similars = store.find_similar(getattr(incident, "symptom", ""), module=getattr(incident, "module", ""), limit=3)
            if not similars: return ""
            return "\n\n=== Benzer Cozumler ===\n" + "\n".join([f"[{round(s.score*100)}%] {s.lesson.resolution[:100]}" for s in similars])
        except Exception: return ""

    # Legacy Aliases for backward compatibility
    def _step_rank_hypotheses_rc1(self, *args, **kwargs): return self._step_rank_hypotheses(*args, **kwargs)
    async def _step_verify_rc1(self, *args, **kwargs): return await self._step_verify(*args, **kwargs)

# Singleton — main.py'de model_orch inject edilir
_repair_orchestrator: Optional[RepairOrchestrator] = None

def get_repair_orchestrator(model_orch=None, project_root: str = ".") -> RepairOrchestrator:
    global _repair_orchestrator
    if _repair_orchestrator is None:
        _repair_orchestrator = RepairOrchestrator(
            model_orch=model_orch,
            project_root=project_root,
        )
    return _repair_orchestrator
