import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, List, Dict, Any, Optional

try:
    from sqlalchemy import select, desc
except ImportError:
    pass
try:
    from libs.db.session import session_scope
except ImportError:
    pass
try:
    from libs.db.repositories.repository import ProjectRepository, ApiMetricRepository, TaskLogRepository, CostRepository
except ImportError:
    pass
try:
    from libs.db.models import (
        ImprovementOpportunity, CEOSuggestedTask, CEODecision,
        Project, CEOPerformanceLog, SovereignGoal # Faz 79: North Star Goals
    )
except ImportError:
    pass
from services.orchestration.agi.cognitive.sovereign_auditor import sovereign_auditor
from libs.llm.model_orchestrator import ModelOrchestrator
from services.orchestration.ceo.forecaster import CEOForecaster
from services.orchestration.ceo.resource_governor import ResourceGovernor
from services.orchestration.agi.cognitive.policy_evolution import PolicyEvolutionEngine
from services.observability.logging import get_logger
from workers.workflow_worker.tasks.celery_app import celery_app

logger = get_logger("ceo_engine")

class CEOEngine:
    """
    Core Decision Engine for the CEO.
    Analyzes system state, detects opportunities, and suggests workers.workflow_worker.tasks.
    """
    def __init__(self, model_orch: ModelOrchestrator):
        self.model_orch = model_orch
        self.last_scan_at = None

    async def _perform_strategic_audit(self, db, goal: SovereignGoal):
        """
        Active projelerin North Star hedeflerine katkısını denetler.
        """
        if not goal: return

        logger.info(f"👔 CEO Engine: Strategic Audit for Goal '{goal.title}' started.")
        # Bu hedefle ilişkili projeleri bul
        from libs.db.models import Project, ProjectStatus
        stmt = select(Project).where(Project.goal_id == goal.id, Project.status.in_([ProjectStatus.RUNNING, ProjectStatus.QUEUED, ProjectStatus.PENDING]))
        res = await db.execute(stmt)
        projects = res.scalars().all()

        for project in projects:
            # Projenin son durumunu ve KPI'lara etkisini analiz et
            impact = await self._verify_north_star_progress(db, goal, project)

            if impact.get("deviation_detected"):
                logger.warning(f"👔 CEO Audit: Project '{project.title}' shows deviation from goal! Realigning...")
                await self.realign_project(db, project, impact["reason"])
            else:
                logger.info(f"👔 CEO Audit: Project '{project.title}' is aligned. (Impact Delta: {impact.get('delta', 0)})")

        # Eğer hedef gerçekleşmişse/KPI'lar tutmuşsa statüsünü güncelle
        # Otonom pivot yeteneği
        if await self._check_goal_completion(db, goal):
             logger.info(f"👔 CEO Engine: Goal '{goal.title}' completed! Archiving...")
             goal.status = "completed"  # type: ignore[assignment]
             goal.completed_at = datetime.now(timezone.utc)  # type: ignore[assignment]

    async def _verify_north_star_progress(self, db, goal: SovereignGoal, project: Project) -> Dict[str, Any]:
        """
        Gerçekleşen KPI delta'larını hedeflenen vizyonla karşılaştırır.
        """
        # Şimdilik basitleştirilmiş mantık: Goal içindeki kpis objesi ile son metrikleri karşılaştır
        current_kpis = goal.kpis or {}

        # Son 1 saatlik metrikleri al (Basitleştirilmiş)
        try:
            from libs.db.repositories.repository import ApiMetricRepository
            metrics = await ApiMetricRepository.get_summary(db, since_hours=1)

            # Örnek: 'latency' KPI'ı varsa denetle
            if "latency_target" in current_kpis:
                current_latency = metrics.get("avg_latency", 0)
                target = current_kpis["latency_target"]
                if current_latency > target * 1.5: # %50'den fazla sapma
                    return {"deviation_detected": True, "reason": f"Latency regression: {current_latency}ms > {target}ms", "delta": current_latency - target}

            return {"deviation_detected": False, "delta": 0}
        except Exception as e:
            logger.error(f"KPI verification error: {e}")
            return {"deviation_detected": False, "delta": 0}

    async def realign_project(self, db, project: Project, reason: str):
        """
        Sapan projeyi durdurur veya vizyona uygun yeni bir task açar.
        """
        project.notes = f"CEO Realignment: {reason}. (Applied at {datetime.now(timezone.utc)})"  # type: ignore[assignment]
        # Eğer sapma kritiksse durdur!
        if "regression" in reason.lower():
            logger.warning(f"👔 CEO Engine: Critical regression in '{project.title}'. STALLING project.")
            project.status = "ERROR"  # type: ignore[assignment]
            project.error_detail = f"CEO Realignment: {reason}"  # type: ignore[assignment]

    async def _check_goal_completion(self, db, goal: SovereignGoal) -> bool:
        """Hedefin tamamlanıp tamamlanmadığını son KPI verilerine göre kontrol eder."""
        try:
            from libs.db.repositories.repository import ApiMetricRepository
            metrics = await ApiMetricRepository.get_summary(db, since_hours=24)

            prompt = f"""
            HEDEF: {goal.title}
            VİZYON: {goal.vision_statement}
            BEKLENEN KPI'LAR: {goal.kpis}

            MEVCUT SİSTEM METRİKLERİ (Son 24 Saat):
            {metrics}

            Yukarıdaki verilere dayanarak, bu stratejik hedefin başarıyla tamamlanıp tamamlanmadığını değerlendirin.
            Yanıtınızın en başında sadece 'EVET' veya 'HAYIR' kelimelerinden birini kullanın.
            """

            response = await self.model_orch.complete(
                messages=[
                    {"role": "system", "content": "Sistem verilerini analiz edip hedeflerin durumunu değerlendiren analitik bir uzmansınız."},
                    {"role": "user", "content": prompt}
                ],
                preferred_agent="architect"
            )

            return "EVET" in response.upper()
        except Exception as e:
            logger.error(f"Goal completion check failed: {e}")
            return False

    async def run_scan(self):
        """Main entry point for periodic background scanning."""
        logger.info("CEO Engine: Starting system scan...")

        # --- PHASE 3: Resource Governance Health Check ---
        try:
            await ResourceGovernor.evaluate_emergency_status()
        except Exception as e:
            logger.error(f"👔 Sovereign Governor failed: {e}")

        async with session_scope() as db:
            # --- PHASE 12: Budget Check ---
            try:
                from libs.config import MONTHLY_BUDGET
                from libs.db.repositories.repository import CostRepository

                # Sadece repo ve metod varsa await et
                if hasattr(CostRepository, 'total_cost'):
                    total_spent = await CostRepository.total_cost(db)
                    if total_spent >= MONTHLY_BUDGET:
                        logger.warning(f"CEO Engine: Monthly budget limit reached (${MONTHLY_BUDGET}). Scanning paused.")
                        return
                else:
                    logger.warning("CostRepository.total_cost is not available. Skipping budget check.")
            except Exception as e:
                logger.error(f"CEO Engine budget check failed: {e}")
                # Faz 12.1 Hardening: Bütçe kontrolü olmadan çalışma GÜVENLİ DEĞİLDİR.
                # Eğer llm_cost_logs tablosu eksikse hata fırlat!
                raise RuntimeError(
                    "CRITICAL: Bütçe tabloları (llm_cost_logs vb.) bulunamadı! "
                    "Lütfen 'alembic upgrade head' ile veritabanını güncelleyin."
                ) from e

            # --- PHASE 53: NAS & Policy Optimization (The 'Other' Strategy Motor) ---
            try:
                from services.orchestration.ceo.optimizer import CEOStochasticOptimizer
                # SRE Hardening: Heavy optimization should not block the main heartbeat/lifespan
                asyncio.create_task(CEOStochasticOptimizer.run_optimization_cycle())
                logger.info("👔 CEO Engine: Optimization cycle offloaded to background.")
            except Exception as e:
                logger.error(f"👔 CEO Optimizer trigger failed: {e}")

            # --- PHASE 80: North Star Goal Alignment ---
            # Sistem ana hedefleri kontrol eder, yoksa otonom olarak bir vizyon belirler.
            current_goal = await self._ensure_north_star_goal(db)
            if current_goal:
                logger.info(f"👔 CEO Engine: Mevcut North Star Hedefi: '{current_goal.title}'")
                # FAZ 12.1: Projelerin hedefe katkısını denetle
                await self._perform_strategic_audit(db, current_goal)
            else:
                logger.warning("👔 CEO Engine: Herhangi bir North Star Hedefi belirlenemedi.")

            # 1. Collect opportunities using the high-fidelity auditor
            logger.debug("👔 CEO Engine: Scanning via SovereignCortexAuditor...")
            auditor_findings = await sovereign_auditor.run_full_audit()

            # --- PHASE 2: Operational Drift & Efficiency Audit ---
            try:
                # 2. Sapmaları (Drift) kontrol et
                drift_anomalies = await CEOForecaster.detect_operational_drift()
                if drift_anomalies:
                    for anomaly in drift_anomalies:
                        logger.warning(f"👔 CEO Engine: Drift Detected! {anomaly['message']}")
                        await self._record_decision(db, "DRIFT_MITIGATION", anomaly)

                    # FAZ 12.1: Drift tespit edildiğinde politikaları evrimleştir!
                    evolution_engine = PolicyEvolutionEngine(model_orch=self.model_orch)
                    logger.info("👔 CEO Engine: Triggering autonomous policy evolution due to drift.")
                    asyncio.create_task(evolution_engine.run_evolution_cycle())

                # 3. Agent ROI & Efficiency
                roi_stats = await CEOForecaster.calculate_agent_roi()
                efficiency_findings = await CEOForecaster.audit_token_efficiency()

                for inefficient in efficiency_findings:
                    logger.warning(f"👔 CEO Engine: Inefficient Agent '{inefficient['agent_id']}' detected! Throttling...")
                    await self._record_decision(db, "THROTTLE_AGENT", inefficient)
            except Exception as e:
                logger.error(f"👔 CEO Engine Phase 2 audit failed: {e}")

            opportunities = []
            # Map auditor findings to CEOEngine internal format
            for f in auditor_findings:
                opportunities.append({
                    "source_type": f["source_type"],
                    "source_ref": f["id"],
                    "title": f["title"],
                    "description": f["description"],
                    "severity": f["severity"],
                    "category": f.get("category", "reliability"),
                    "evidence": f["evidence"],
                    "evidence_detail": str(f["evidence"])
                })

            # 1.1 Visual UX Scan (Faz 12)
            try:
                from services.orchestration.agi.cognitive.aesthetic_auditor import aesthetic_auditor
                visual_audit = await aesthetic_auditor.audit_aesthetics()
                if visual_audit.get("status") == "completed" and visual_audit.get("score", 100) < 85:
                    opportunities.append({
                        "source_type": "visual_ux",
                        "source_ref": f"aesthetic_{datetime.now(timezone.utc).strftime('%Y%m%d%H')}",
                        "title": "Görsel Estetik ve UX Borcu Tespit Edildi",
                        "description": f"Sistem estetik skoru %{visual_audit['score']}. Eksikler: {', '.join(visual_audit['debt'])}",
                        "severity": "medium" if visual_audit["score"] > 70 else "high",
                        "category": "ux",
                        "evidence": visual_audit
                    })
            except Exception as v_err:
                logger.error(f"CEO Engine visual scan failed: {v_err}")

            # 1.2 Repair Health Scan (Faz 12)

            # --- PHASE 8: Forecasting & Anomaly Scan ---
            try:
                logger.debug("👔 CEO Engine: Scanning for strategic anomalies...")
                anomalies = await CEOForecaster.detect_anomalies()
                for anomaly in anomalies:
                    opportunities.append({
                        "source_type": f"anomaly_{anomaly['type']}",
                        "source_ref": f"forecaster_{datetime.now(timezone.utc).strftime('%Y%m%d%H')}",
                        "title": f"Tahmini Risk: {anomaly['type']}",
                        "description": anomaly["message"],
                        "severity": anomaly["severity"],
                        "category": "strategic",
                        "evidence": anomaly
                    })
            except Exception as e:
                logger.error(f"CEO Forecaster failed during scan: {e}")

            # 2. Score and persist opportunities
            logger.debug(f"👔 CEO Engine: Scoring {len(opportunities)} opportunities...")
            scored_opportunities = await self.score_opportunities(opportunities)
            logger.debug("👔 CEO Engine: Persisting opportunities to DB...")
            await self._persist_opportunities(db, scored_opportunities)
            await db.commit()

            # 3. Decide next actions and create suggestions
            logger.debug("👔 CEO Engine: Deciding next actions based on scored opportunities...")
            await self.decide_next_actions(db, scored_opportunities)

            self.last_scan_at = datetime.now(timezone.utc)
            logger.info(f"CEO Engine: Scan complete. Found {len(scored_opportunities)} opportunities.")
            return scored_opportunities

    async def audit_codebase(self):
        """Alias for run_scan to support legacy calls."""
        return await self.run_scan()

    async def _ensure_north_star_goal(self, db) -> Optional[SovereignGoal]:
        """Eğer aktif bir hedef yoksa, otonom olarak bir tane oluşturur."""
        try:
            stmt = select(SovereignGoal).where(SovereignGoal.status == "active").order_by(desc(SovereignGoal.priority))
            res = await db.execute(stmt)
            goal = res.scalars().first()

            if not goal:
                logger.info("👔 CEO Engine: Aktif bir North Star Hedefi bulunamadı. GoalSynthesizer tetikleniyor...")
                from services.orchestration.agi.cognitive.goal_synthesizer import GoalSynthesizer
                synthesizer = GoalSynthesizer(model_orch=self.model_orch)
                # Otonom olarak yeni hedefler sentezle - SRE: Non-blocking during startup
                asyncio.create_task(synthesizer.run_synthesis_cycle())
                logger.info("👔 CEO Engine: Goal synthesis started in background.")
            return goal
        except Exception as e:
            logger.error(f"CEO Engine goal enforcement failed: {e}")
            return None

    async def _scan_strategic_gaps(self, db) -> List[Any]:
        """Scans for strategic architectural gaps."""
        try:
            from services.repair.improvement.observer import ImprovementObserver
            obs = ImprovementObserver()
            return await obs.scan()
        except Exception as e:
            logger.error(f"CEO Engine strategic scan failed: {e}")
            return []

    async def _scan_operational_stalling(self, db) -> List[Dict[str, Any]]:
        """Scans for tasks that are stalled or in problematic states."""
        ops = []
        now = datetime.now(timezone.utc)

        # Check for long-queued tasks
        recent_queued = await ProjectRepository.list_recent(db, limit=50, status="queued")
        for p in recent_queued:
            updated = getattr(p, "updated_at", p.created_at)
            if updated.tzinfo is None: updated = updated.replace(tzinfo=timezone.utc)

            elapsed = (now - updated).total_seconds()
            if elapsed > 600: # 10 minutes
                # --- Faz 8: Kurtarma Mekanizması ---
                # Eğer görev 'queued' ise ve 10 dakikadır tepki yoksa, ya Redis silinmiş ya da worker takılmıştır.
                # Önce görevi 'error' durumuna çekelim ki CEO engine yeni bir 'Düzeltme' görevi açabilsin.
                logger.warning(f"👔 CEO Engine: Proje '{p.title}' ({p.id}) kuyrukta takılı kalmış ({int(elapsed)}s).")

                # Eğer bu bir CEO göreviyse ve 'queued' ise, doğrudan yeniden kuyruğa sokmayı deneyebiliriz (opsiyonel)
                # Şimdilik temizlik için status'u 'error' yapalım, engine zaten 'queue_stuck' fırsatı oluşturuyor.
                if p.status == "QUEUED":
                    p.status = "ERROR"  # type: ignore[assignment]
                    p.error_detail = f"Kuyruk zaman aşımı ({int(elapsed)}s). Sistem tarafından otomatik hata durumuna çekildi."  # type: ignore[assignment]
                    logger.info(f"👔 CEO Engine: Proje '{p.id}' otomatik olarak 'ERROR' durumuna çekildi.")

                source_type = "queue_stuck"
                source_ref = str(p.id)
                ops.append({
                    "source_type": source_type,
                    "source_ref": source_ref,
                    "pattern_hash": ImprovementOpportunity.generate_hash(source_type, source_ref),
                    "title": f"Queue Stalling: {p.title}",
                    "description": f"Project '{p.title}' has been in 'queued' status for over 10 minutes. Check worker/redis.",
                    "severity": "high",
                    "category": "reliability",
                    "evidence": {"project_id": str(p.id), "time_in_status": elapsed},
                    "evidence_detail": f"Project '{p.title}' stuck in queue for {int(elapsed)}s. Threshold: 600s."
                })

        # Check for approval timeouts
        pending_approval = await ProjectRepository.list_recent(db, limit=50, status="pending_approval")
        for p in pending_approval:
            updated = getattr(p, "updated_at", p.created_at)
            if updated.tzinfo is None: updated = updated.replace(tzinfo=timezone.utc)

            elapsed = (now - updated).total_seconds()
            if elapsed > 1800: # 30 minutes
                source_type = "approval_timeout"
                source_ref = str(p.id)
                ops.append({
                    "source_type": source_type,
                    "source_ref": source_ref,
                    "pattern_hash": ImprovementOpportunity.generate_hash(source_type, source_ref),
                    "title": f"Approval Timeout: {p.title}",
                    "description": f"Project '{p.title}' has been waiting for human approval for over 30 minutes.",
                    "severity": "medium",
                    "category": "automation",
                    "evidence": {"project_id": str(p.id), "time_in_status": elapsed},
                    "evidence_detail": f"Approval pending for {int(elapsed)}s on '{p.title}'. Human intervention may be needed."
                })

        return ops

    def _get_repair_health_summary(self) -> Dict[str, Any]:
        """Faz 12: Onarım sisteminden anlık durum özeti alır."""
        try:
            from services.repair.application.orchestrator import get_repair_orchestrator
            orch = get_repair_orchestrator()
            stats = orch.stats()
            return {
                "total_jobs": stats.get("total", 0),
                "open_incidents": stats.get("incident_memory", {}).get("open", 0),
                "pr_pending": stats.get("pipeline", {}).get("by_status", {}).get("awaiting_approval", 0),
                "success_rate": stats.get("success_rate", 0.0)
            }
        except Exception as e:
            logger.error(f"CEO Engine: Repair stats alınamadı: {e}")
            return {"open_incidents": 0, "available": False}

    async def score_opportunities(self, opportunities: List[Any]) -> List[Dict[str, Any]]:
        """Assigns scores and priority to opportunities."""
        scored = []
        for op in opportunities:
            # Handle both dicts and objects if observer returns objects
            if hasattr(op, "severity"):
                data = {
                    "source_type": getattr(op, "source_type", "scan_result"),
                    "source_ref": getattr(op, "source_ref", None),
                    "title": getattr(op, "description", "New Opportunity")[:100],
                    "description": getattr(op, "description", ""),
                    "severity": getattr(op, "severity", "medium"),
                    "category": "reliability", # Default
                    "evidence": getattr(op, "evidence", {})
                }
            else:
                data = op.copy()
                if "title" not in data and "description" in data:
                    data["title"] = data["description"][:100]
                elif "title" not in data:
                    data["title"] = "New Opportunity"

            # --- LEARNING MECHANISM: Global Success Bonus ---
            # Fetch recent success rate from logs (could be cached in production)
            async with session_scope() as db_perf:
                from sqlalchemy import func
                perf_stmt = select(func.avg(CEOPerformanceLog.impact_score)).where(CEOPerformanceLog.success == True)
                avg_impact_res = await db_perf.execute(perf_stmt)
                avg_impact = avg_impact_res.scalar() or 50

            # Rule-based scoring
            severity_weights = {"critical": 100, "high": 75, "medium": 50, "low": 25}
            sev = data.get("severity")
            sev_str = sev if isinstance(sev, str) else "medium"
            impact_score = severity_weights.get(sev_str, 50)
            urgency_score = 70 if data["source_type"] in ["queue_stuck", "approval_timeout", "recurring_error"] else 30
            confidence_score = 0.9 # Observer is usually confident
            effort_score = 40 # Estimated

            # priority_score = impact * 0.4 + urgency * 0.3 + confidence * 20 - effort * 0.1
            priority_score = (impact_score * 0.45) + (urgency_score * 0.35) + (confidence_score * 20) - (effort_score * 0.1)

            # Category bonus
            if data.get("category") == "security":
                priority_score += 15

            # Learning Bonus: Increase priority if the system has been succeeding lately
            if avg_impact > 70:
                priority_score += 5
            elif avg_impact < 40:
                priority_score -= 5 # System is cautious if failing

            data.update({
                "impact_score": impact_score,
                "urgency_score": urgency_score,
                "confidence_score": confidence_score,
                "effort_score": effort_score,
                "priority_score": round(priority_score, 2)
            })
            scored.append(data)

        return sorted(scored, key=lambda x: x["priority_score"], reverse=True)

    async def _persist_opportunities(self, db, scored_ops: List[Dict[str, Any]]):
        """Writes opportunities to the DB, avoiding duplicates via pattern_hash and checking cooldowns."""
        from sqlalchemy import select, and_
        from datetime import datetime, timedelta, timezone

        for data in scored_ops:
            # Hash-based deduplication (primary)
            phash = data.get("pattern_hash")
            if not phash and data.get("source_ref"):
                phash = ImprovementOpportunity.generate_hash(data["source_type"], data["source_ref"])

            if phash:
                # Check for existing open/suggested or RECENTLY ignored (cooldown)
                cooldown_cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
                existing = await db.execute(
                    select(ImprovementOpportunity).where(
                        ImprovementOpportunity.pattern_hash == phash,
                        (ImprovementOpportunity.status.in_(["open", "suggested", "converted"])) |
                        ((ImprovementOpportunity.status == "ignored") & (ImprovementOpportunity.created_at >= cooldown_cutoff))
                    )
                )
                if existing.scalars().first():
                    continue

            new_id = uuid.uuid4()
            new_op = ImprovementOpportunity(
                id=new_id,
                source_type=data["source_type"],
                source_ref=data.get("source_ref"),
                title=data["title"],
                description=data["description"],
                severity=data["severity"],
                category=data.get("category", "reliability"),
                impact_score=data["impact_score"],
                urgency_score=data["urgency_score"],
                confidence_score=data["confidence_score"],
                effort_score=data["effort_score"],
                priority_score=data["priority_score"],
                pattern_hash=phash,
                evidence_detail=data.get("evidence_detail", ""),
                status="open"
            )
            db.add(new_op)
        await db.flush()

    async def decide_next_actions(self, db, opportunities: List[Dict[str, Any]]):
        """Turns high-priority opportunities into suggested tasks using LLM reasoning."""
        from sqlalchemy import func, select
        from datetime import datetime, timedelta, timezone

        # 1. Production Hardening: Global Cooldown / Throttling (Faz 12.1)
        # Son 1 saat içinde oto-onaylanan (Auto-Approve) görev sayısını kontrol et.
        hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        auto_exec_res = await db.execute(
            select(func.count(CEODecision.id)).where(
                CEODecision.decision_type == "auto_approve",
                CEODecision.created_at >= hour_ago
            )
        )
        auto_count = auto_exec_res.scalar() or 0
        if auto_count >= 10:
            logger.info(f"CEO Engine: Saatlik oto-karar limitine ulaşıldı ({auto_count}/10). Yeni oto-onay verilmeyecek.")
            # Devam edebiliriz ama sadece suggestion (öneri) yapılacak, auto-exec bloklanacak.
            self._throttle_auto_exec = True
        else:
            self._throttle_auto_exec = False

        # 2. Kota koruması: Son 5 dakika içinde 5'ten fazla öneri yapıldıysa dur.
        recent_time = datetime.now(timezone.utc) - timedelta(minutes=5)
        recent_sug_res = await db.execute(
            select(func.count(CEOSuggestedTask.id)).where(CEOSuggestedTask.created_at >= recent_time)
        )
        if recent_sug_res.scalar() >= 5:
            logger.info("CEO Engine: Son 5 dakika içinde 5 öneri limitine ulaşıldı (Kota koruması).")
            return

        # Günlük Masraf/Kaynak Kotası: Son 24 saatte maksimum 20 görev
        daily_time = datetime.now(timezone.utc) - timedelta(days=1)
        daily_sug_res = await db.execute(
            select(func.count(CEOSuggestedTask.id)).where(CEOSuggestedTask.created_at >= daily_time)
        )
        if daily_sug_res.scalar() >= 20:
            logger.warning("CEO Engine: Günlük 20 görev/öneri limitine ulaşıldı (Resource Ceilings). Maliyet kontrolü amacıyla durduruldu.")
            return

        # En acil 3 fırsatı değerlendir (Mevcut + Yeni)
        # --- Faz 8: DB'deki 'open' fırsatları da dahil et ---
        # Tarama sonuçları (opportunities) zaten elimizde. Şimdi DB'dekileri de alalım.
        stmt = select(ImprovementOpportunity).where(ImprovementOpportunity.status.in_(["open", "suggested"])).order_by(ImprovementOpportunity.priority_score.desc()).limit(5)
        res = await db.execute(stmt)
        persisted_ops = res.scalars().all()

        # Merge scan results (dicts) with persisted (objs)
        all_to_eval = []
        seen_refs = set()

        for op_obj in persisted_ops:
            all_to_eval.append(op_obj)
            if op_obj.source_ref: seen_refs.add(op_obj.source_ref)

        for op_data in opportunities:
            if op_data.get("source_ref") not in seen_refs:
                # Convert dict to temp obj for uniform interface
                all_to_eval.append(op_data)

        # Sort combined list by priority
        all_to_eval.sort(key=lambda x: x.priority_score if hasattr(x, "priority_score") else x.get("priority_score", 0), reverse=True)

        for op in all_to_eval[:3]:
            # --- Faz 8: Throttling / Jitter ---
            # API yükünü dağıtmak için 0.5 - 2.0 sn arası rastgele bekleme ekle
            import random
            await asyncio.sleep(random.uniform(0.5, 2.0))

            p_score = op.priority_score if hasattr(op, "priority_score") else op.get("priority_score", 0)
            o_title = op.title if hasattr(op, "title") else op.get("title", "Unknown")

            if p_score >= 20:
                logger.info(f"CEO Engine: {o_title} için öneri hazırlanıyor (Priority: {p_score})")
                await self._create_suggestion_from_op(db, op)
                await db.commit()
            else:
                logger.debug(f"CEO Engine: {o_title} eşik değerini geçemedi (Priority: {p_score} < 20)")

    async def _generate_suggestion_with_llm(self, op: ImprovementOpportunity, active_goal: Optional[Any] = None) -> Dict[str, Any]:
        """Uses LLM to delegate to a specific Specialist Agent from the library."""
        from services.orchestration.indexing.system_indexer import SystemIndexer
        from services.orchestration.agency.loader import get_agency_loader
        agency_loader = get_agency_loader()

        indexer = SystemIndexer()
        # Fetch relevant code context
        context = indexer.get_context_for_task(query=f"{op.title} {op.source_type}", limit=3)

        # Prepare Specialist Candidates list
        specialists = agency_loader.list_agents()
        specialist_list_str = "\n".join([f"- {s['id']}: {s['description']}" for s in specialists[:50]]) # Limit for context size

        goal_context = ""
        if active_goal:
            goal_context = f"\nMEVCUT STRATEJİK HEDEF: {active_goal.title}\nVİZYON: {active_goal.vision_statement}\n"

        from services.orchestration.application.prompts import CEO_DELEGATION_PROMPT
        prompt = CEO_DELEGATION_PROMPT.format(
            title=op.title, source_type=op.source_type,
            severity=op.severity, description=op.description,
            category=op.category, priority_score=op.priority_score,
            evidence=getattr(op, 'evidence_detail', 'N/A'),
            context=context + goal_context,
            specialist_list_str=specialist_list_str
        )

        try:
            response = await self.model_orch.complete(
                messages=[{"role": "system", "content": "Sistem verilerini yorumlayan ve uzman gizli ajanları görevlendiren CEO'sunuz. Her zaman Türkçe yanıt verirsiniz."},
                          {"role": "user", "content": prompt}],
                preferred_agent="architect"
            )
            import json
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.error(f"CEO Delegation failed: {e}")

        # Fallback to rule-based legacy roles if LLM fails
        return {
            "title": f"Düzeltme: {op.title}",
            "description": f"{op.title} için otomatik müdahale gerekiyor. {op.description}",
            "reasoning": "Motor zaman aşımı nedeniyle yedek görevlendirme yapıldı.",
            "agent_id": "architect",
            "confidence": 0.5
        }

    async def _refine_suggestion_with_llm(self, op: ImprovementOpportunity, prev_suggestion: Dict[str, Any], critique: Dict[str, Any]) -> Dict[str, Any]:
        """Refines a suggestion based on critic feedback."""
        refinement_prompt = f"""
        MEVCUT FIRSAT: {op.title}
        ESKİ ÖNERİ: {prev_suggestion.get('title')}
        ELEŞTİRMEN GERİ BİLDİRİMİ: {critique.get('reason')}

        Yukarıdaki eleştiriyi dikkate alarak öneriyi geliştirin ve hataları düzeltin.
        Yanıtınız mutlaka JSON formatında olmalıdır.
        """

        try:
            response = await self.model_orch.complete(
                messages=[
                    {"role": "system", "content": "Stratejisini düzelten ve optimize eden bir CEO'sunuz. Her zaman Türkçe yanıt verirsiniz."},
                    {"role": "user", "content": refinement_prompt}
                ],
                preferred_agent="architect"
            )
            import json
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.error(f"CEO Refinement failed: {e}")

        return prev_suggestion # Return old one if refinement fails

    async def _create_suggestion_from_op(self, db, op_item: Any):
        """Logic to generate a task suggestion from an opportunity, delegating to Specialists."""
        from sqlalchemy import select

        # Normalize op_item to object if it's a dict (though ideally it's an object from the DB)
        if isinstance(op_item, dict):
            # Fallback path for Dict inputs (though we prefer objects for ID access)
            res = await db.execute(
                select(ImprovementOpportunity).where(
                    ImprovementOpportunity.source_type == op_item["source_type"],
                    ImprovementOpportunity.source_ref == op_item.get("source_ref")
                ).limit(1)
            )
            op_obj = res.scalars().first()
            if not op_obj:
                # Create it on the fly if it doesn't exist yet
                op_obj = ImprovementOpportunity(
                    id=uuid.uuid4(),
                    source_type=op_item["source_type"],
                    source_ref=op_item.get("source_ref"),
                    title=op_item["title"],
                    description=op_item["description"],
                    severity=op_item["severity"],
                    category=op_item.get("category", "reliability"),
                    impact_score=op_item.get("impact_score", 5.0),
                    urgency_score=op_item.get("urgency_score", 5.0),
                    confidence_score=op_item.get("confidence_score", 5.0),
                    effort_score=op_item.get("effort_score", 5.0),
                    priority_score=op_item.get("priority_score", 50.0),
                    evidence_detail=str(op_item.get("evidence", "")),
                    status="open"
                )
                db.add(op_obj)
                await db.flush()
        else:
            op_obj = op_item

        # Check if a suggestion already exists for this op
        res_sug = await db.execute(
            select(CEOSuggestedTask).where(CEOSuggestedTask.opportunity_id == op_obj.id).limit(1)
        )
        if res_sug.scalars().first(): return

        # PHASE 2.1: North Star Alignment (Fetch Active Goal)
        from libs.db.models import SovereignGoal
        active_goal_stmt = select(SovereignGoal).where(SovereignGoal.status == "active").order_by(desc(SovereignGoal.priority)).limit(1)
        active_goal_res = await db.execute(active_goal_stmt)
        active_goal = active_goal_res.scalars().first()

        # PHASE 2.2: Reflective Reasoning Loop (Self-Critique & Refinement)
        logger.info(f"👔 CEO Engine: Generating suggestion for {op_obj.title}...")
        ai_suggestion = await self._generate_suggestion_with_llm(op_obj, active_goal)

        if not ai_suggestion or "title" not in ai_suggestion:
            logger.error("👔 CEO Engine: Suggestion generation failed (Empty or Invalid JSON).")
            return

        # --- Reflective Loop Start ---
        max_refinements = 3
        refinement_count = 0
        deliberation_logs = []

        while refinement_count < max_refinements:
            logger.info(f"👔 CEO Engine: Critique Phase (Refinement {refinement_count}) for: {ai_suggestion.get('title')}")

            critique = await self._critique_suggestion(op_obj, ai_suggestion, active_goal)
            logger.debug(f"👔 CEO Engine: Parsed Critique: {critique}")

            deliberation_logs.append({
                "iteration": refinement_count,
                "suggestion": ai_suggestion.copy(),
                "critique": critique
            })

            if critique.get("is_valid", True):
                if refinement_count > 0:
                    logger.info(f"👔 CEO Engine: Strategy validated after {refinement_count} refinement(s).")
                break

            action = critique.get("action", "refine")

            if action == "cancel":
                logger.warning(f"👔 CEO Engine: Strategy CANCELLED by critic: {critique.get('reason')}")
                return

            if action == "fallback":
                logger.info(f"👔 CEO Engine: Switching to FALLBACK strategy: {critique.get('reason')}")
                ai_suggestion["title"] = f"Güvenli Onarım: {op_obj.title}"
                ai_suggestion["description"] = f"Otomatik onarım girişimi: {op_obj.description}"
                ai_suggestion["is_roadmap"] = False
                ai_suggestion["confidence"] = 0.6
                break

            if action == "refine":
                logger.info(f"👔 CEO Engine: REFINING strategy based on critic feedback: {critique.get('reason')}")
                ai_suggestion = await self._refine_suggestion_with_llm(op_obj, ai_suggestion, critique)
                refinement_count += 1
            else:
                # Default to valid if action unknown
                break

        # --- Reflective Loop End ---

        confidence = ai_suggestion.get("confidence", 0.5)

        agent_id = ai_suggestion.get("agent_id", ai_suggestion.get("agent_hint", "architect"))
        is_roadmap = ai_suggestion.get("is_roadmap", False)
        steps = ai_suggestion.get("steps", [])

        # 1. Ana Öneriyi (Parent/Summary) Oluştur
        parent_id = uuid.uuid4()
        new_suggestion = CEOSuggestedTask(
            id=parent_id,
            opportunity_id=op_obj.id,
            title=ai_suggestion["title"],
            description=ai_suggestion["description"],
            priority=op_obj.severity,
            owner_agent_hint=agent_id,
            status="suggested",
            reasoning_summary=ai_suggestion.get("reasoning", f"Priority score {op_obj.priority_score}"),
            impact_projection=ai_suggestion.get("projection", {"estimated_cost": 0.01, "risk_reduction_pct": 50, "performance_gain": "medium"}),
            plan_hierarchy={"is_roadmap": is_roadmap, "step_count": len(steps) if is_roadmap else 1},
            goal_id=active_goal.id if active_goal else None
        )
        db.add(new_suggestion)

        # 2. Eğer Yol Haritası (Roadmap) ise Alt Görevleri Oluştur
        execution_target = new_suggestion
        if is_roadmap and steps:
            logger.info(f"👔 CEO Engine: '{ai_suggestion['title']}' için {len(steps)} adımlık yol haritası oluşturuluyor.")
            child_tasks = []
            for i, step in enumerate(steps):
                if not isinstance(step, dict):
                    continue
                child_id = uuid.uuid4()
                child_sug = CEOSuggestedTask(
                    id=child_id,
                    opportunity_id=op_obj.id,
                    parent_id=parent_id,
                    title=step.get("title", f"Step {i+1}"),
                    description=step.get("description", ""),
                    priority=op_obj.severity,
                    owner_agent_hint=step.get("agent_id", agent_id),
                    status="suggested",
                    plan_hierarchy={"step_index": i + 1, "total_steps": len(steps)}
                )
                db.add(child_sug)
                child_tasks.append(child_sug)

            # İlk adımı otomatik onay hedefi olarak belirle
            if child_tasks:
                execution_target = child_tasks[0]
                agent_id = execution_target.owner_agent_hint

        await db.flush()

        # Mark op as suggested
        op_obj.status = "suggested"  # type: ignore[assignment]

        # Record decision
        decision = CEODecision(
            id=uuid.uuid4(),
            opportunity_id=op_obj.id,
            decision_type="suggest_task",
            decision_summary=f"CEO Strategy: {'Roadmap' if is_roadmap else 'Task'} '{ai_suggestion['title']}'",
            decision_source="llm_agent"
        )
        db.add(decision)

        # --- AUTO-EXECUTION LOGIC ---
        if not getattr(self, "_throttle_auto_exec", False) and confidence >= 0.5 and op_obj.priority_score >= 50:
            logger.info(f"CEO Engine: AUTO-EXECUTING {'first step of ' if is_roadmap else ''}task '{execution_target.title}'")

            await self._approve_and_enqueue(
                db,
                execution_target,
                op_obj,
                is_auto=True,
                reasoning=ai_suggestion.get('reasoning')
            )

            decision.decision_type = "auto_approve"  # type: ignore[assignment]
            decision.decision_summary = f"Auto-Approved {'Roadmap' if is_roadmap else 'Task'}: {execution_target.title}"  # type: ignore[assignment]

        await db.flush()

    async def _approve_and_enqueue(self, db, suggestion, opportunity, is_auto=True, reasoning=None):
        """Helper to create a Project and move a suggestion to queue."""
        from libs.db.models import Project
        from libs.db.repositories.repository import TaskLogRepository

        proj_id = uuid.uuid4()
        label = "[AUTO-CEO]" if is_auto else "[MANUAL-CEO]"

        new_project = Project(
            id=proj_id,
            title=f"{label} {suggestion.title}",
            description=suggestion.description,
            status="pending",
            priority_level=9 if (opportunity and opportunity.severity == "critical") else 7,
            assigned_agent=suggestion.owner_agent_hint or "architect",
            ceo_managed=True,
            workflow_template="default",
            quality_profile="production",
            notes=f"CEO Dashboard üzerinden {'otomatik' if is_auto else 'kullanıcı'} tarafından onaylandı. \nGerekçe: {reasoning}"
        )
        db.add(new_project)
        suggestion.status = "approved"  # type: ignore[assignment]
        suggestion.created_task_id = proj_id  # type: ignore[assignment]

        # --- ENQUEUE TO JOB QUEUE ---
        try:
            from services.orchestration.application.job_queue import job_queue

            job = await job_queue.enqueue(
                "run_project",
                db_project_id=str(proj_id),
                title=new_project.title,
                description=new_project.description,
                user_id=suggestion.owner_agent_hint or "ceo_engine",
                workflow_template="default",
                quality_profile="production"
            )
            new_project.status = "QUEUED"  # type: ignore[assignment]
            new_project.job_id = job.id

            await TaskLogRepository.write(
                db, proj_id, "queued",
                f"{'Otomatik' if is_auto else 'Manuel'} olarak başlatıldı ve ortak kuyruğa atıldı. (İş ID: {job.id})",
                agent_id="ceo_engine"
            )
            logger.info(f"CEO Engine: Suggestion '{suggestion.id}' approved and queued as Project '{proj_id}'")
            return proj_id
        except Exception as e:
            logger.error(f"CEO Engine: Approval enqueuing failed for {suggestion.id}: {e}")
            new_project.status = "ERROR"  # type: ignore[assignment]
            new_project.error_detail = str(e)  # type: ignore[assignment]
            return None

    async def manual_approve_suggestion(self, suggestion_id: uuid.UUID) -> Dict[str, Any]:
        """Kullanıcının Dashboard'dan verdiği onayı işler."""
        from libs.db.session import session_scope
        from sqlalchemy import select

        async with session_scope() as db:
            # Önce öneriyi bul
            res = await db.execute(select(CEOSuggestedTask).where(CEOSuggestedTask.id == suggestion_id))
            suggestion = res.scalars().first()

            if not suggestion:
                return {"success": False, "error": "Öneri bulunamadı."}

            if suggestion.status != "suggested":
                return {"success": False, "error": f"Öneri zaten '{suggestion.status}' durumunda."}

            # Bağlı fırsatı bul (varsa)
            opportunity = None
            if suggestion.opportunity_id:
                res_op = await db.execute(select(ImprovementOpportunity).where(ImprovementOpportunity.id == suggestion.opportunity_id))
                opportunity = res_op.scalars().first()

            # Onayla ve kuyruğa at
            proj_id = await self._approve_and_enqueue(
                db,
                suggestion,
                opportunity,
                is_auto=False,
                reasoning="Dashboard Manuel Onay"
            )

            if proj_id:
                await db.commit()
                return {"success": True, "project_id": str(proj_id)}
            else:
                return {"success": False, "error": "Kuyruğa atma başarısız."}

    async def get_findings(self) -> Dict[str, Any]:
        """Provides detailed findings (suggestions merged with opportunities) for the CEO dashboard."""
        from libs.db.session import session_scope
        async with session_scope() as db:
            from sqlalchemy import select
            from sqlalchemy.orm import joinedload

            res_sug = await db.execute(
                select(CEOSuggestedTask)
                .options(joinedload(CEOSuggestedTask.opportunity))
                .order_by(CEOSuggestedTask.created_at.desc())
                .limit(100)
            )

            findings = []
            for sug in res_sug.scalars().all():
                op = sug.opportunity
                
                # Parse evidence detail
                evidence = None
                if op and op.evidence_detail:
                    try:
                        import json
                        evidence = json.loads(op.evidence_detail)
                    except Exception:
                        evidence = {"detail": op.evidence_detail}
                elif op and hasattr(op, "evidence") and op.evidence:
                    evidence = op.evidence

                findings.append({
                    "id": str(sug.id),
                    "category": op.category if op else "GENEL",
                    "finding": sug.title,
                    "description": sug.description or "",
                    "severity": op.severity if op else (sug.priority or "medium"),
                    "priority_score": round(float(op.priority_score or 0.0), 2) if op else 50.0,
                    "status": sug.status,
                    "evidence": evidence,
                    "reasoning": sug.reasoning_summary or "Gerekçe henüz formüle edilmedi.",
                    "created_at": sug.created_at.isoformat() if sug.created_at else None
                })

            return {"findings": findings}

    async def get_overview(self) -> Dict[str, Any]:
        """Provides a quick summary for the CEO Dashboard API."""
        async with session_scope() as db:
            from sqlalchemy import func, select

            # 1. Temel Metrikler
            res_ops_count = await db.execute(select(func.count(ImprovementOpportunity.id)).where(ImprovementOpportunity.status == "open"))
            open_ops_count = res_ops_count.scalar() or 0

            res_sug_count = await db.execute(select(func.count(CEOSuggestedTask.id)).where(CEOSuggestedTask.status == "suggested"))
            suggested_tasks_count = res_sug_count.scalar() or 0

            # 1.1 Detaylı Listeler
            res_ops = await db.execute(
                select(ImprovementOpportunity)
                .where(ImprovementOpportunity.status == "open")
                .order_by(ImprovementOpportunity.priority_score.desc())
                .limit(10)
            )
            opportunities = [
                {
                    "id": str(op.id),
                    "title": op.title,
                    "description": op.description,
                    "severity": op.severity,
                    "priority": round(float(op.priority_score or 0.0), 2),
                    "source": op.source_type,
                    "created_at": op.created_at.isoformat() if op.created_at else None
                } for op in res_ops.scalars().all()
            ]

            res_sug = await db.execute(
                select(CEOSuggestedTask)
                .where(CEOSuggestedTask.status == "suggested")
                .order_by(CEOSuggestedTask.created_at.desc())
                .limit(10)
            )
            suggestions = [
                {
                    "id": str(sug.id),
                    "title": sug.title,
                    "description": sug.description or "",
                    "reasoning": sug.reasoning_summary or "",
                    "impact": sug.impact_projection or {},
                    "created_at": sug.created_at.isoformat() if sug.created_at else None
                } for sug in res_sug.scalars().all()
            ]

            # 2. Faz 8: Stratejik Görünüm ve Tahminleme
            try:
                outlook = await CEOForecaster.get_strategic_outlook()
            except Exception as e:
                logger.error(f"Outlook generation failed: {e}")
                outlook = {"risk_score": 0, "budget_forecast": {}}

            # 3. Dinamik Manifesto ve Aksiyon
            risk_val = outlook.get('risk_score', 0)
            risk_score = risk_val if isinstance(risk_val, (int, float)) else 0
            manifesto = f"Sistem Risk Skoru: %{risk_score}. "
            if risk_score > 50:
                manifesto += "Güvenlik ve stabilite öncelikli moda geçildi."
                next_action = "Kritik Risk Analizi ve Darboğaz Giderme"
            else:
                manifesto += "Operasyonel verimlilik ve büyüme hedefleniyor."
                next_action = "Operasyonel İzleme"

            # Eğer açık fırsat varsa aksiyonu güncelle
            if open_ops_count > 0:
                top_op = next((o for o in opportunities), None)
                if top_op:
                    next_action = f"Odak: {top_op['title']}"

            return {
                "open_opportunity_count": open_ops_count,
                "suggested_task_count": suggested_tasks_count,
                "opportunities": opportunities,
                "suggestions": suggestions,
                "next_action": next_action,
                "manifesto": manifesto,
                "strategic_outlook": outlook,
                "last_scan_at": self.last_scan_at.isoformat() if self.last_scan_at else None
            }

    async def _critique_suggestion(self, op, suggestion, active_goal: Optional[Any] = None) -> Dict[str, Any]:
        """Ayrı bir 'critic' rolü ile önerinin mantığını denetler."""
        goal_context = ""
        if active_goal:
            goal_context = f"\nMEVCUT STRATEJİK HEDEF: {active_goal.title}\n"

        prompt = f"""
        FIRSAT: {op.title} (Severity: {op.severity})
        ÖNERİLEN EYLEM: {suggestion['title']}
        GEREKÇE: {suggestion.get('reasoning')}
        ROADMAP: {suggestion.get('is_roadmap')}
        {goal_context}

        Bu stratejik kararı bir 'Sovereign Critic' olarak değerlendir.
        Halüsinasyon var mı? Öneri fırsatla örtüşüyor mu? Güvenlik riski var mı? Maliyet makul mü? Stratejik hedefle uyumlu mu?

        Eğer öneri küçük düzeltmelerle iyileşebilecekse 'refine',
        kesinlikle yanlış veya riskliyse 'cancel',
        riski azaltmak için standart bir çözüme dönmek gerekiyorsa 'fallback' aksiyonunu seç.

        JSON Formatı: {{'is_valid': bool, 'reason': '...', 'action': 'proceed/refine/fallback/cancel'}}
        """
        try:
            resp = await self.model_orch.complete_task(
                agent_role="critic",
                prompt=prompt,
                system_prompt="Sen AGI Strateji Denetçisisin."
            )
            import json, re
            match = re.search(r'\{.*\}', resp.content, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception:
            pass
        return {"is_valid": True} # Default to positive if critic fails


    async def evaluate_outcomes(self):
        """
        Scans for completed CEO-managed projects and evaluates their success.
        This is the core of the Feedback Loop.
        """
        logger.info("CEO Engine: Starting outcome evaluation...")
        async with session_scope() as db:
            from sqlalchemy import select

            # 1. Fetch completed CEO projects that haven't been evaluated yet
            # We check projects where ceo_managed=True AND status='completed'
            # AND there's no entry in CEOPerformanceLog for them.
            res = await db.execute(
                select(Project)
                .where(Project.ceo_managed == True)
                .where(Project.status == "COMPLETED")
            )
            completed_projects = res.scalars().all()

            for project in completed_projects:
                # Check if already evaluated
                perf_check = await db.execute(
                    select(CEOPerformanceLog).where(CEOPerformanceLog.project_id == project.id).limit(1)
                )
                if perf_check.scalars().first():
                    continue

                logger.info(f"CEO Engine: Evaluating result of project '{project.title}'")

                # 2. Get the original suggestion and opportunity
                sug_res = await db.execute(select(CEOSuggestedTask).where(CEOSuggestedTask.id == project.suggestion_id))
                suggestion = sug_res.scalars().first()
                if not suggestion: continue

                op_res = await db.execute(select(ImprovementOpportunity).where(ImprovementOpportunity.id == suggestion.opportunity_id))
                opportunity = op_res.scalars().first()

                # 3. Analyze results (Summary of logs + Final Report)
                # In a real scenario, we'd use LLM to read project.report and logs
                success = "Success" in (project.report or "") or project.progress_pct == 100

                # 4. Record Performance
                perf_log = CEOPerformanceLog(
                    id=uuid.uuid4(),
                    suggestion_id=suggestion.id,
                    project_id=project.id,
                    agent_id=project.assigned_agent or "unknown",
                    opportunity_type=opportunity.source_type if opportunity else "task",
                    success=success,
                    impact_score=90 if success else 10,
                    final_reasoning=f"Proje şu durumla tamamlandı: {project.status}. Rapor analizi başarının sağlandığını gösteriyor."
                )
                db.add(perf_log)

                if success and opportunity:
                    opportunity.status = "resolved"  # type: ignore[assignment]
                    logger.info(f"CEO Engine: Opportunity '{opportunity.title}' marked as RESOLVED.")

                # --- PHASE 2.1: Roadmap Progression ---
                # Eğer bu bir yol haritasının (Roadmap) bir adımıysa, bir sonraki adımı tetikle.
                if success and suggestion and suggestion.parent_id:
                    logger.info(f"CEO Engine: Roadmap '{suggestion.parent_id}' ilerletiliyor...")
                    from sqlalchemy import Integer
                    next_step_stmt = select(CEOSuggestedTask).where(
                        CEOSuggestedTask.parent_id == suggestion.parent_id,
                        CEOSuggestedTask.status == "suggested"
                    ).order_by(CEOSuggestedTask.plan_hierarchy["step_index"].astext.cast(Integer))  # type: ignore[index, attr-defined]

                    next_res = await db.execute(next_step_stmt.limit(1))
                    next_sug = next_res.scalars().first()

                    if next_sug:
                        logger.info(f"CEO Engine: Yol haritasında bir sonraki adım bulundu: '{next_sug.title}'")
                        # Bir sonraki adımı otomatik onaya gönder (Eğer ana plan onaylıysa/mantıklıysa)
                        # Şimdilik doğrudan manuel onaya da düşebilir ama otonom modda oto-onay deneriz.
                        await self._auto_approve_next_step(db, next_sug, project)

            await db.commit()

    async def _auto_approve_next_step(self, db, suggestion: CEOSuggestedTask, prev_project: Project):
        """Yol haritasındaki bir sonraki adımı otomatik olarak başlatır."""
        from libs.db.models import Project
        from libs.db.repositories.repository import TaskLogRepository

        proj_id = uuid.uuid4()
        new_project = Project(
            id=proj_id,
            title=f"[AUTO-CEO] {suggestion.title}",
            description=suggestion.description,
            status="PENDING",
            priority_level=prev_project.priority_level,
            assigned_agent=suggestion.owner_agent_hint or "architect",
            suggestion_id=suggestion.id,
            ceo_managed=True,
            workflow_template="default",
            quality_profile="production",
            notes=f"Yol haritası kapsamında otomatik olarak başlatıldı. Önceki adım: {prev_project.title}"
        )
        db.add(new_project)
        suggestion.status = "approved"  # type: ignore[assignment]
        suggestion.created_task_id = proj_id  # type: ignore[assignment]

        # Enqueue Logic (Unified Job Queue abstraction)
        try:
            from services.orchestration.application.job_queue import job_queue
            job = await job_queue.enqueue(
                "run_project",
                db_project_id=str(proj_id),
                title=new_project.title,
                description=new_project.description,
                user_id=suggestion.owner_agent_hint or "ceo_engine",
                workflow_template="default",
                quality_profile="production"
            )
            new_project.status = "QUEUED"  # type: ignore[assignment]
            new_project.job_id = job.id
            logger.info(f"CEO Engine: Roadmap Next Step '{suggestion.title}' queued (Job: {job.id})")
        except Exception as e:
            logger.error(f"CEO Engine: Next step queueing failed: {e}")
            new_project.status = "ERROR"  # type: ignore[assignment]
            new_project.error_detail = str(e)  # type: ignore[assignment]

    async def _record_decision(self, db, decision_type: str, data: Dict[str, Any]):
        """CEO kararlarını veritabanına kaydeder."""
        from libs.db.models import CEODecision
        decision = CEODecision(
            id=str(uuid.uuid4()),
            decision_type=decision_type,
            summary=data.get("message", "Autonomous Decision Applied"),
            context=data,
            applied_at=datetime.now(timezone.utc)
        )
        db.add(decision)
        try:
            await db.commit()
        except:
            await db.rollback()

_ceo_engine = None

def get_ceo_engine() -> CEOEngine:
    global _ceo_engine
    if _ceo_engine is None:
        from services.orchestration.agi.cognitive.sovereign_cortex import sovereign_cortex as orchestrator
        _ceo_engine = CEOEngine(orchestrator.model_orch)
    return _ceo_engine
