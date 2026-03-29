import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any

try:
    from sqlalchemy import select, desc
except ImportError:
    pass
try:
    from db.session import session_scope
except ImportError:
    pass
try:
    from db.repository import ProjectRepository, ApiMetricRepository, TaskLogRepository, CostRepository
except ImportError:
    pass
try:
    from db.models import ImprovementOpportunity, CEOSuggestedTask, CEODecision, Project, CEOPerformanceLog
except ImportError:
    pass
from improve.observer import ImprovementObserver
from improve.visual_observer import VisualUXObserver
from llm.model_orchestrator import ModelOrchestrator
from core.forecaster import CEOForecaster
from observability.logging import get_logger
from tasks.celery_app import celery_app

logger = get_logger("ceo_engine")

class CEOEngine:
    """
    Core Decision Engine for the CEO.
    Analyzes system state, detects opportunities, and suggests tasks.
    """
    def __init__(self, model_orch: ModelOrchestrator):
        self.model_orch = model_orch
        self.last_scan_at = None

    async def run_scan(self):
        """Main entry point for periodic background scanning."""
        logger.info("CEO Engine: Starting system scan...")
        async with session_scope() as db:
            # --- PHASE 12: Budget Check ---
            try:
                from config import MONTHLY_BUDGET
                from db.repository import CostRepository
                
                # Sadece repo ve metod varsa await et
                if hasattr(CostRepository, 'total_cost'):
                    total_spent = await CostRepository.total_cost(db)
                    if total_spent >= MONTHLY_BUDGET:
                        logger.warning(f"CEO Engine: Monthly budget limit reached (${MONTHLY_BUDGET}). Scanning paused.")
                        return
                else:
                    logger.warning("CostRepository.total_cost is not available. Skipping budget check.")
            except Exception as e:
                # UndefinedTableError (llm_cost_logs tablosu yoksa) durumunda sessizce atla
                if "relation" in str(e) and "does not exist" in str(e):
                    logger.warning("CEO Engine: llm_cost_logs table not found. Skipping budget check (migrations pending).")
                else:
                    logger.error(f"CEO Engine budget check failed: {e}")

            # 1. Collect opportunities using the observer
            observer = ImprovementObserver(db)
            logger.debug("👔 CEO Engine: Scanning via ImprovementObserver...")
            opportunities = await observer.scan()
            
            # 1.1 Visual UX Scan (Faz 12)
            try:
                visual_obs = VisualUXObserver(db, self.model_orch)
                visual_ops = await visual_obs.scan()
                if visual_ops:
                    logger.info(f"👔 CEO Engine: Found {len(visual_ops)} visual/UX opportunities.")
                    opportunities.extend(visual_ops)
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
            
            # 3. Decide next actions and create suggestions
            logger.debug("👔 CEO Engine: Deciding next actions based on scored opportunities...")
            await self.decide_next_actions(db, scored_opportunities)
            
            self.last_scan_at = datetime.now(timezone.utc)
            logger.info(f"CEO Engine: Scan complete. Found {len(scored_opportunities)} opportunities.")
            return scored_opportunities

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
                if p.status == "queued":
                    p.status = "error"
                    p.error_detail = f"Kuyruk zaman aşımı ({int(elapsed)}s). Sistem tarafından otomatik hata durumuna çekildi."
                    logger.info(f"👔 CEO Engine: Proje '{p.id}' otomatik olarak 'error' durumuna çekildi.")

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
            from core.repair_orchestrator import get_repair_orchestrator
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
            impact_score = severity_weights.get(data["severity"], 50)
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
        if auto_count >= 3:
            logger.info(f"CEO Engine: Saatlik oto-karar limitine ulaşıldı ({auto_count}/3). Yeni oto-onay verilmeyecek.")
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

        # En acil 3 fırsatı değerlendir
        for op_data in opportunities[:3]:
            # --- Faz 8: Throttling / Jitter ---
            # API yükünü dağıtmak için 0.5 - 2.0 sn arası rastgele bekleme ekle
            import random
            await asyncio.sleep(random.uniform(0.5, 2.0))
            
            # Eşik değerini 50'ye düşürdük
            if op_data["priority_score"] >= 50:
                logger.info(f"CEO Engine: {op_data['title']} için öneri hazırlanıyor (Priority: {op_data['priority_score']})")
                await self._create_suggestion_from_op(db, op_data)
            else:
                logger.debug(f"CEO Engine: {op_data['title']} eşik değerini geçemedi (Priority: {op_data['priority_score']} < 50)")

    async def _generate_suggestion_with_llm(self, op: ImprovementOpportunity) -> Dict[str, str]:
        """Uses LLM to delegate to a specific Specialist Agent from the library."""
        from core.system_indexer import SystemIndexer
        from core.agency.loader import agency_loader
        
        indexer = SystemIndexer()
        # Fetch relevant code context
        context = indexer.get_context_for_task(query=f"{op.title} {op.source_type}", limit=3)

        # Prepare Specialist Candidates list
        specialists = agency_loader.list_agents()
        specialist_list_str = "\n".join([f"- {s['id']}: {s['description']}" for s in specialists[:50]]) # Limit for context size

        from core.prompts import CEO_DELEGATION_PROMPT
        prompt = CEO_DELEGATION_PROMPT.format(
            title=op.title, source_type=op.source_type,
            severity=op.severity, description=op.description,
            category=op.category, priority_score=op.priority_score,
            evidence=getattr(op, 'evidence_detail', 'N/A'),
            context=context, specialist_list_str=specialist_list_str
        )
        
        try:
            response = await self.model_orch.complete(
                messages=[{"role": "system", "content": "Sistem verilerini yorumlayan ve uzman gizli ajanları görevlendiren CEO'sunuz. Her zaman Türkçe yanıt verirsiniz."},
                          {"role": "user", "content": prompt}],
                preferred_agent="architect",
                task_id="ceo-delegation-v5"
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

    async def _create_suggestion_from_op(self, db, op_data: Dict[str, Any]):
        """Logic to generate a task suggestion from an opportunity, delegating to Specialists."""
        # Find the DB object for this opportunity to get the ID
        from sqlalchemy import select
        res = await db.execute(
            select(ImprovementOpportunity).where(
                ImprovementOpportunity.source_type == op_data["source_type"],
                ImprovementOpportunity.source_ref == op_data.get("source_ref"),
                ImprovementOpportunity.status == "open"
            ).limit(1)
        )
        op_obj = res.scalars().first()
        if not op_obj: return
        
        # Check if a suggestion already exists for this op
        res_sug = await db.execute(
            select(CEOSuggestedTask).where(CEOSuggestedTask.opportunity_id == op_obj.id).limit(1)
        )
        if res_sug.scalars().first(): return

        # Use LLM for intelligent interpretation and delegation
        ai_suggestion = await self._generate_suggestion_with_llm(op_obj)
        confidence = ai_suggestion.get("confidence", 0.5)
        agent_id = ai_suggestion.get("agent_id", ai_suggestion.get("agent_hint", "architect"))

        new_suggestion = CEOSuggestedTask(
            id=uuid.uuid4(),
            opportunity_id=op_obj.id,
            title=ai_suggestion["title"],
            description=ai_suggestion["description"],
            priority=op_obj.severity,
            owner_agent_hint=agent_id,
            status="suggested",
            reasoning_summary=ai_suggestion.get("reasoning", f"Priority score {op_obj.priority_score}"),
            impact_projection=ai_suggestion.get("projection", {"estimated_cost": 0.01, "risk_reduction_pct": 50, "performance_gain": "medium"})
        )
        db.add(new_suggestion)
        await db.flush()
        
        # Mark op as suggested
        op_obj.status = "suggested"
        
        # Record decision
        decision = CEODecision(
            id=uuid.uuid4(),
            opportunity_id=op_obj.id,
            decision_type="suggest_task",
            decision_summary=f"CEO Strategy: Suggested '{ai_suggestion['title']}'",
            decision_source="llm_agent"
        )
        db.add(decision)
        
        # --- AUTO-EXECUTION LOGIC ---
        # If confidence and priority are high enough, approve automatically
        # Faz 12.1: throttle_auto_exec kontrolü eklendi
        if not getattr(self, "_throttle_auto_exec", False) and confidence >= 0.9 and op_obj.priority_score >= 60:
            logger.info(f"CEO Engine: AUTO-EXECUTING task '{ai_suggestion['title']}' due to satisfied confidence ({confidence})")
            
            # Use a mock/internal call to the approve endpoint logic or refactor to shared method
            from db.models import Project
            from db.repository import TaskLogRepository
            
            proj_id = uuid.uuid4()
            new_project = Project(
                id=proj_id,
                title=f"[AUTO-CEO] {ai_suggestion['title']}",
                description=ai_suggestion["description"],
                status="pending", # Initially pending, then queued by celery call
                priority_level=9 if op_obj.severity == "critical" else 7,
                assigned_agent=agent_id,
                suggestion_id=new_suggestion.id,
                ceo_managed=True,
                workflow_template="default",
                quality_profile="production",
                notes=f"CEO Motoru tarafından otomatik olarak yetkilendirildi. \nGerekçe: {ai_suggestion.get('reasoning')}"
            )
            db.add(new_project)
            new_suggestion.status = "approved"
            new_suggestion.created_task_id = proj_id
            
            decision.decision_type = "auto_approve"
            decision.decision_summary = f"Auto-Approved: {ai_suggestion['title']}"
            
            # --- ENQUEUE TO CELERY ---
            try:
                kwargs = {
                    "workflow_template": "default",
                    "quality_profile": "production",
                    "acceptance_criteria": ["CEO Engine otomasyon projesinin hedefine ulaşması."]
                }
                celery_task = celery_app.send_task(
                    "run_project_task",
                    args=[str(proj_id), new_project.title, new_project.description],
                    kwargs=kwargs
                )
                new_project.status = "queued"
                new_project.job_id = celery_task.id
                
                await TaskLogRepository.write(
                db, proj_id, "queued",
                    "Otomatik onaylanan görev Celery worker'a gönderildi.",
                    agent_id="ceo_engine"
                )
            except Exception as e:
                logger.error(f"CEO Engine: Auto-Approval enqueuing failed for {new_project.id}: {e}")
                new_project.status = "error"
                new_project.error_detail = str(e)
                # Keep as pending if celery fails, will be caught by stalling scan later

        await db.flush()

    async def get_overview(self) -> Dict[str, Any]:
        """Provides a quick summary for the CEO Dashboard API."""
        async with session_scope() as db:
            from sqlalchemy import func, select
            
            # 1. Temel Metrikler
            res_ops = await db.execute(select(func.count(ImprovementOpportunity.id)).where(ImprovementOpportunity.status == "open"))
            open_ops = res_ops.scalar() or 0
            
            res_sug = await db.execute(select(func.count(CEOSuggestedTask.id)).where(CEOSuggestedTask.status == "suggested"))
            suggested_tasks = res_sug.scalar() or 0
            
            # 2. Faz 8: Stratejik Görünüm ve Tahminleme
            try:
                outlook = await CEOForecaster.get_strategic_outlook()
            except Exception as e:
                logger.error(f"Outlook generation failed: {e}")
                outlook = {"risk_score": 0, "budget_forecast": {}}

            # 3. Dinamik Manifesto ve Aksiyon
            manifesto = f"Sistem Risk Skoru: %{outlook.get('risk_score', 0)}. "
            if outlook.get('risk_score', 0) > 50:
                manifesto += "Güvenlik ve stabilite öncelikli moda geçildi."
                next_action = "Kritik Risk Analizi ve Darboğaz Giderme"
            else:
                manifesto += "Operasyonel verimlilik ve büyüme hedefleniyor."
                next_action = "Operasyonel İzleme"

            # Eğer açık fırsat varsa aksiyonu güncelle
            if open_ops > 0:
                res_top = await db.execute(
                    select(ImprovementOpportunity)
                    .where(ImprovementOpportunity.status == "open")
                    .order_by(ImprovementOpportunity.priority_score.desc())
                    .limit(1)
                )
                top_op = res_top.scalars().first()
                if top_op:
                    next_action = f"Odak: {top_op.title}"

            return {
                "open_opportunity_count": open_ops,
                "suggested_task_count": suggested_tasks,
                "next_action": next_action,
                "manifesto": manifesto,
                "strategic_outlook": outlook,
                "last_scan_at": self.last_scan_at.isoformat() if self.last_scan_at else None
            }

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
                .where(Project.status == "completed")
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
                
                # 5. Close the Loop: Mark opportunity as resolved if successful
                if success and opportunity:
                    opportunity.status = "resolved"
                    logger.info(f"CEO Engine: Opportunity '{opportunity.title}' marked as RESOLVED.")
            
            await db.commit()

_ceo_engine = None

def get_ceo_engine() -> CEOEngine:
    global _ceo_engine
    if _ceo_engine is None:
        from core.orchestrator import orchestrator
        _ceo_engine = CEOEngine(orchestrator.model_orch)
    return _ceo_engine
