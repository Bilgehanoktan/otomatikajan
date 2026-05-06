"""
Self-Improvement Observer (Consolidated from improvement_v1)
[CONSOLIDATION] Eski improvement_v1/observer.py'nin aktif versiyonu.
Sistemdeki iyilestirme firsatlarini tarar.
"""

import uuid
from typing import Any, Dict, List

from libs.db.models.core_models import ImprovementOpportunity
from services.observability.logging import get_logger

logger = get_logger("improvement.observer")


class ImprovementObserver:
    CLASS_FILE_HINTS = {
        "architect": "services/orchestration/domain/auditor.py",
        "self_governor": "services/orchestration/domain/auditor.py",
        "deerflow_planner": "services/orchestration/agi/cognitive/agi_goal_decomposer.py",
        "planner": "services/orchestration/agi/cognitive/agi_goal_decomposer.py",
        "backend_dev": "services/orchestration/application/operational_executor.py",
        "frontend_dev": "apps/refine_control_plane/src/app/workflows/_components/WorkflowDetailClient.tsx",
        "qa_engineer": "services/orchestration/application/operational_executor.py",
        "security": "services/repair/domain/recovery_strategies.py",
        "devops": "services/repair/domain/recovery_strategies.py",
        "critic": "services/orchestration/domain/auditor.py",
    }

    async def scan(self) -> List[ImprovementOpportunity]:
        """Sistemi tarar ve iyilestirme firsatlarini bulur."""
        logger.info("ImprovementObserver: Sistem taraniyor...")
        opportunities: List[ImprovementOpportunity] = []

        try:
            opportunities.extend(await self._scan_agent_failures())
            opportunities.extend(await self._scan_endpoint_errors())
            opportunities.extend(await self._scan_workflow_queue_health())
            opportunities.extend(await self._scan_approval_bottlenecks())
            opportunities.extend(await self._scan_incident_backlog())
            opportunities.extend(await self._scan_improvement_pipeline_health())
            opportunities.extend(await self._scan_llm_provider_pressure())
        except Exception as e:
            logger.error(f"Observer scan hatasi: {e}")

        return opportunities

    async def scan_for_issues(self) -> List[Dict[str, Any]]:
        """Eski API uyumlulugu — core/improvement/gate.py tarafindan kullanilir."""
        opportunities = await self.scan()
        return [
            {
                "agent_id": opp.id,
                "reason": opp.description,
                "severity": opp.severity,
                "affected_files": opp.affected_files,
                "evidence": getattr(opp, "evidence_detail", ""),
            }
            for opp in opportunities
        ]

    async def _scan_agent_failures(self) -> List[ImprovementOpportunity]:
        """Agent basari oranlarini ve hata desenlerini tarar."""
        from datetime import datetime, timedelta, timezone

        from libs.db.models.core_models import ImprovementOpportunity, WorkflowEvent
        from libs.db.session import AsyncSessionLocal, is_db_degraded
        from sqlalchemy import String, cast, func, select

        opportunities: List[ImprovementOpportunity] = []
        logger.info("Agent hatalari taraniyor...")

        try:
            async with AsyncSessionLocal() as session:
                yesterday = datetime.now(timezone.utc) - timedelta(days=1)

                from libs.db.models.core_models import SubTask

                is_postgres = not is_db_degraded()
                if is_postgres:
                    target_file_col = SubTask.input_data["target_file"].as_string()
                    id_comparison = cast(SubTask.id, String) == WorkflowEvent.step_id
                else:
                    target_file_col = func.json_extract(SubTask.input_data, "$.target_file")
                    id_comparison = func.replace(cast(SubTask.id, String), "-", "") == func.replace(
                        WorkflowEvent.step_id, "-", ""
                    )

                stmt = (
                    select(
                        func.min(WorkflowEvent.step_id).label("sample_step_id"),
                        WorkflowEvent.payload["error"].as_string().label("error_msg"),
                        func.count().label("err_count"),
                        target_file_col.label("target_file"),
                        SubTask.agent_id.label("agent_id"),
                    )
                    .join(SubTask, id_comparison, isouter=True)
                    .where(WorkflowEvent.event_type == "step_failed")
                    .where(WorkflowEvent.created_at >= yesterday)
                    .group_by("error_msg", "target_file", "agent_id")
                    .having(func.count() >= 1)
                )

                res = await session.execute(stmt)
                for row in res.all():
                    _, error_msg, count, target_file, agent_id = row
                    role = (agent_id or "unknown").strip()
                    pattern_hash = ImprovementOpportunity.generate_hash("agent_failure", f"{role}:{error_msg}")

                    clean_file = target_file.strip('"') if target_file else None
                    if not clean_file and error_msg and "not registered" in error_msg.lower():
                        clean_file = "libs/workflow/runner.py"
                    if not clean_file:
                        clean_file = self.CLASS_FILE_HINTS.get(role)

                    affected_files = [clean_file] if clean_file and clean_file != "null" else []
                    if count >= 10:
                        severity = "critical"
                    elif count >= 5:
                        severity = "high"
                    else:
                        severity = "medium"

                    opportunities.append(
                        ImprovementOpportunity(
                            id=uuid.uuid4(),
                            source_type="agent_failure",
                            source_ref=role,
                            title=f"Recurring Failure in class: {role}",
                            description=f"Detected {count} failures in {role} with error: {error_msg}",
                            severity=severity,
                            category="reliability",
                            evidence_detail=error_msg,
                            pattern_hash=pattern_hash,
                            affected_files=affected_files,
                            status="open",
                        )
                    )

        except Exception as e:
            logger.error(f"Agent failure scanning failed: {e}")

        return opportunities

    async def _scan_endpoint_errors(self) -> List[ImprovementOpportunity]:
        """API endpoint hata oranlarini tarar (401/404/429 pattern-aware)."""
        from datetime import datetime, timedelta, timezone

        from libs.db.models.core_models import ApiMetric, ImprovementOpportunity
        from libs.db.session import AsyncSessionLocal
        from sqlalchemy import case, func, select

        opportunities: List[ImprovementOpportunity] = []
        logger.info("Endpoint hatalari taraniyor (401/404/429)...")

        endpoint_class_hints = {
            "auth": "apps/refine_control_plane/src/lib/auth.ts",
            "workflow": "apps/refine_control_plane/src/app/workflows/_components/WorkflowDetailClient.tsx",
            "approvals": "apps/refine_control_plane/src/app/approvals/page.tsx",
            "incidents": "apps/refine_control_plane/src/app/incidents/page.tsx",
            "escalations": "apps/refine_control_plane/src/app/governance/escalations/page.tsx",
            "repair_lab": "apps/refine_control_plane/src/app/repair-lab/page.tsx",
            "health": "apps/refine_control_plane/src/app/page.tsx",
            "training": "apps/refine_control_plane/src/app/training/page.tsx",
            "lineage": "apps/refine_control_plane/src/app/governance-lineage/page.tsx",
            "governance": "apps/refine_control_plane/src/app/governance-lineage/page.tsx",
            "mesh": "apps/refine_control_plane/src/app/mesh/page.tsx",
            "other": "services/api/routes",
        }

        min_hits = {401: 8, 404: 5, 429: 3}
        status_meta = {
            401: {
                "code": "AUTH_401",
                "category": "authentication",
                "base_title": "Authentication/session churn",
                "base_severity": "medium",
            },
            404: {
                "code": "NOTFOUND_404",
                "category": "contract",
                "base_title": "Missing endpoint / route mismatch",
                "base_severity": "medium",
            },
            429: {
                "code": "RATELIMIT_429",
                "category": "capacity",
                "base_title": "Rate-limit pressure detected",
                "base_severity": "high",
            },
        }

        try:
            async with AsyncSessionLocal() as session:
                since = datetime.now(timezone.utc) - timedelta(hours=24)

                endpoint_class = case(
                    (ApiMetric.endpoint.like("/api/v1/auth/%"), "auth"),
                    (ApiMetric.endpoint.like("/api/v1/workflows%"), "workflow"),
                    (ApiMetric.endpoint.like("/api/v1/governance/approvals%"), "approvals"),
                    (ApiMetric.endpoint.like("/api/v1/governance/incidents%"), "incidents"),
                    (ApiMetric.endpoint.like("/api/v1/governance/escalations%"), "escalations"),
                    (ApiMetric.endpoint.like("/api/v1/governance/ops/%"), "escalations"),
                    (ApiMetric.endpoint.like("/api/v1/repair-lab/%"), "repair_lab"),
                    (ApiMetric.endpoint.like("/api/v1/health/%"), "health"),
                    (ApiMetric.endpoint.like("/api/v1/governance/inbox/governor/%"), "escalations"),
                    (ApiMetric.endpoint.like("/api/v1/governance/drills%"), "training"),
                    (ApiMetric.endpoint.like("/api/v1/governance/lineage%"), "lineage"),
                    (ApiMetric.endpoint.like("/api/v1/governance/%"), "governance"),
                    (ApiMetric.endpoint.like("/api/v1/mesh/%"), "mesh"),
                    else_="other",
                ).label("endpoint_class")

                stmt = (
                    select(
                        endpoint_class,
                        ApiMetric.status_code,
                        func.count(ApiMetric.id).label("hit_count"),
                        func.count(func.distinct(ApiMetric.endpoint)).label("endpoint_count"),
                        func.min(ApiMetric.endpoint).label("sample_endpoint"),
                    )
                    .where(ApiMetric.created_at >= since)
                    .where(ApiMetric.status_code.in_([401, 404, 429]))
                    .group_by(endpoint_class, ApiMetric.status_code)
                )

                result = await session.execute(stmt)
                for row in result.all():
                    ep_class, status_code, hit_count, endpoint_count, sample_endpoint = row
                    status_code = int(status_code)
                    hit_count = int(hit_count or 0)
                    endpoint_count = int(endpoint_count or 0)
                    meta = status_meta.get(status_code)

                    if not meta:
                        continue
                    if hit_count < min_hits.get(status_code, 1):
                        continue

                    severity = meta["base_severity"]
                    if hit_count >= 25 or (status_code == 429 and hit_count >= 10):
                        severity = "high"
                    if hit_count >= 60:
                        severity = "critical"

                    source_ref = f"{ep_class}:{meta['code']}"
                    pattern_hash = ImprovementOpportunity.generate_hash("endpoint_error_pattern", source_ref)
                    affected_file = endpoint_class_hints.get(ep_class, endpoint_class_hints["other"])

                    opportunities.append(
                        ImprovementOpportunity(
                            id=uuid.uuid4(),
                            source_type="endpoint_error_pattern",
                            source_ref=source_ref,
                            title=f"{meta['base_title']} [{ep_class}]",
                            description=(
                                f"{ep_class} endpoint sinifinda son 24 saatte "
                                f"{hit_count} adet HTTP {status_code} goruldu. "
                                "Pattern endpoint davranisi icin iyilestirme gerektiriyor."
                            ),
                            severity=severity,
                            category=meta["category"],
                            evidence_detail=(
                                f"status={status_code} class={ep_class} hits_24h={hit_count} "
                                f"unique_endpoints={endpoint_count} sample={sample_endpoint or '-'}"
                            ),
                            pattern_hash=pattern_hash,
                            affected_files=[affected_file] if affected_file else [],
                            status="open",
                        )
                    )
        except Exception as e:
            logger.error(f"Endpoint scanning failed: {e}")

        return opportunities

    async def _scan_workflow_queue_health(self) -> List[ImprovementOpportunity]:
        """Workflow kuyruğunda adım oluşmama / uzun bekleme desenlerini tarar."""
        from datetime import datetime, timedelta, timezone

        from libs.db.models.core_models import Project, SubTask
        from libs.db.session import AsyncSessionLocal
        from sqlalchemy import String, cast, func, select

        opportunities: List[ImprovementOpportunity] = []
        logger.info("Workflow queue sagligi taraniyor...")

        try:
            async with AsyncSessionLocal() as session:
                now = datetime.now(timezone.utc)
                horizon = now - timedelta(days=3)
                status_expr = func.lower(cast(Project.status, String))

                stmt = (
                    select(
                        Project.id,
                        Project.title,
                        status_expr.label("status_lower"),
                        Project.created_at,
                        func.count(SubTask.id).label("subtask_count"),
                        func.max(SubTask.updated_at).label("last_subtask_update"),
                    )
                    .outerjoin(SubTask, SubTask.project_id == Project.id)
                    .where(Project.created_at >= horizon)
                    .where(
                        status_expr.in_(
                            [
                                "pending",
                                "queued",
                                "waiting",
                                "resuming",
                                "retrying",
                                "running",
                                "pending_approval",
                                "waiting_approval",
                            ]
                        )
                    )
                    .group_by(Project.id, Project.title, status_expr, Project.created_at)
                )

                rows = (await session.execute(stmt)).all()

                no_step_ids: List[str] = []
                stalled_ids: List[str] = []
                no_step_samples: List[str] = []
                stalled_samples: List[str] = []

                for row in rows:
                    project_id, title, status_lower, created_at, subtask_count, last_subtask_update = row
                    age_min = max(0.0, (now - created_at).total_seconds() / 60.0) if created_at else 0.0

                    if subtask_count == 0 and status_lower in {"pending", "queued", "resuming", "waiting"} and age_min >= 10:
                        no_step_ids.append(str(project_id))
                        if len(no_step_samples) < 5:
                            no_step_samples.append(f"{title or str(project_id)}({int(age_min)}m)")
                        continue

                    reference_update = last_subtask_update or created_at
                    stale_min = (
                        max(0.0, (now - reference_update).total_seconds() / 60.0) if reference_update else 0.0
                    )
                    if status_lower in {"running", "waiting", "retrying", "resuming"} and stale_min >= 20:
                        stalled_ids.append(str(project_id))
                        if len(stalled_samples) < 5:
                            stalled_samples.append(f"{title or str(project_id)}({int(stale_min)}m)")

                if no_step_ids:
                    severity = "high" if len(no_step_ids) >= 8 else "medium"
                    opportunities.append(
                        ImprovementOpportunity(
                            id=uuid.uuid4(),
                            source_type="workflow_queue_health",
                            source_ref="queued_without_steps",
                            title="Queued workflows are waiting without planned steps",
                            description=(
                                f"Son taramada {len(no_step_ids)} workflow kuyrukta bekliyor ancak step olusmadi."
                            ),
                            severity=severity,
                            category="workflow",
                            evidence_detail=f"sample={', '.join(no_step_samples)}",
                            pattern_hash=ImprovementOpportunity.generate_hash(
                                "workflow_queue_health", "queued_without_steps"
                            ),
                            affected_files=[
                                "services/workflow_api/router.py",
                                "libs/workflow/runner.py",
                                "apps/refine_control_plane/src/app/workflows/_components/WorkflowDetailClient.tsx",
                            ],
                            status="open",
                        )
                    )

                if stalled_ids:
                    severity = "critical" if len(stalled_ids) >= 6 else "high"
                    opportunities.append(
                        ImprovementOpportunity(
                            id=uuid.uuid4(),
                            source_type="workflow_queue_health",
                            source_ref="running_stalled",
                            title="Active workflows appear stalled",
                            description=f"Son taramada {len(stalled_ids)} workflow uzun sure ilerleme gosteremedi.",
                            severity=severity,
                            category="workflow",
                            evidence_detail=f"sample={', '.join(stalled_samples)}",
                            pattern_hash=ImprovementOpportunity.generate_hash(
                                "workflow_queue_health", "running_stalled"
                            ),
                            affected_files=[
                                "services/workflow_api/router.py",
                                "services/orchestration/agi/operational/kinetic_arbiter.py",
                            ],
                            status="open",
                        )
                    )
        except Exception as e:
            logger.error(f"Workflow queue health scanning failed: {e}")

        return opportunities

    async def _scan_approval_bottlenecks(self) -> List[ImprovementOpportunity]:
        """Approval pipeline birikimini tarar."""
        from datetime import datetime, timedelta, timezone

        from libs.db.models.core_models import ApprovalRequest
        from libs.db.session import AsyncSessionLocal
        from sqlalchemy import String, cast, func, select

        opportunities: List[ImprovementOpportunity] = []
        logger.info("Approval bottleneck taramasi yapiliyor...")

        try:
            async with AsyncSessionLocal() as session:
                now = datetime.now(timezone.utc)
                since = now - timedelta(hours=24)
                status_expr = func.lower(cast(ApprovalRequest.status, String))

                stmt = (
                    select(
                        ApprovalRequest.request_type,
                        func.count(ApprovalRequest.id).label("pending_count"),
                        func.min(ApprovalRequest.created_at).label("oldest_pending"),
                    )
                    .where(ApprovalRequest.created_at >= since)
                    .where(status_expr == "pending")
                    .group_by(ApprovalRequest.request_type)
                )

                rows = (await session.execute(stmt)).all()
                for row in rows:
                    req_type, pending_count, oldest_pending = row
                    pending_count = int(pending_count or 0)
                    if pending_count < 4:
                        continue

                    wait_min = (
                        int((now - oldest_pending).total_seconds() / 60.0)
                        if oldest_pending
                        else 0
                    )
                    severity = "high" if pending_count >= 10 or wait_min >= 90 else "medium"

                    opportunities.append(
                        ImprovementOpportunity(
                            id=uuid.uuid4(),
                            source_type="approval_bottleneck",
                            source_ref=f"{req_type or 'unknown'}:pending",
                            title=f"Approval bottleneck detected ({req_type or 'unknown'})",
                            description=(
                                f"{pending_count} adet bekleyen approval request birikti. "
                                f"En eski bekleme suresi: {wait_min} dakika."
                            ),
                            severity=severity,
                            category="governance",
                            evidence_detail=f"request_type={req_type} pending={pending_count} oldest_wait_min={wait_min}",
                            pattern_hash=ImprovementOpportunity.generate_hash(
                                "approval_bottleneck", f"{req_type or 'unknown'}:pending"
                            ),
                            affected_files=[
                                "services/workflow_api/governance_router.py",
                                "apps/refine_control_plane/src/app/approvals/page.tsx",
                            ],
                            status="open",
                        )
                    )
        except Exception as e:
            logger.error(f"Approval bottleneck scanning failed: {e}")

        return opportunities

    async def _scan_incident_backlog(self) -> List[ImprovementOpportunity]:
        """Operasyonel incident backlog desenlerini tarar."""
        from datetime import datetime, timedelta, timezone

        from libs.db.models.core_models import OperationalIncident
        from libs.db.session import AsyncSessionLocal
        from sqlalchemy import String, cast, func, select

        opportunities: List[ImprovementOpportunity] = []
        logger.info("Incident backlog taramasi yapiliyor...")

        try:
            async with AsyncSessionLocal() as session:
                now = datetime.now(timezone.utc)
                since = now - timedelta(days=2)
                status_expr = func.lower(cast(OperationalIncident.status, String))

                stmt = (
                    select(
                        OperationalIncident.incident_type,
                        func.count(OperationalIncident.id).label("open_count"),
                        func.min(OperationalIncident.created_at).label("oldest_open"),
                    )
                    .where(OperationalIncident.created_at >= since)
                    .where(status_expr.in_(["open", "active", "investigating"]))
                    .group_by(OperationalIncident.incident_type)
                )

                rows = (await session.execute(stmt)).all()
                for row in rows:
                    incident_type, open_count, oldest_open = row
                    open_count = int(open_count or 0)
                    if open_count < 3:
                        continue

                    age_min = int((now - oldest_open).total_seconds() / 60.0) if oldest_open else 0
                    severity = "critical" if open_count >= 10 else "high" if open_count >= 6 else "medium"

                    opportunities.append(
                        ImprovementOpportunity(
                            id=uuid.uuid4(),
                            source_type="incident_backlog",
                            source_ref=f"{incident_type or 'unknown'}:open",
                            title=f"Incident backlog pressure ({incident_type or 'unknown'})",
                            description=(
                                f"{open_count} adet acik incident tespit edildi. "
                                f"En eski acik kayit {age_min} dakikadir kapanmadi."
                            ),
                            severity=severity,
                            category="reliability",
                            evidence_detail=f"incident_type={incident_type} open_count={open_count} oldest_age_min={age_min}",
                            pattern_hash=ImprovementOpportunity.generate_hash(
                                "incident_backlog", f"{incident_type or 'unknown'}:open"
                            ),
                            affected_files=[
                                "services/workflow_api/governance_router.py",
                                "apps/refine_control_plane/src/app/incidents/page.tsx",
                            ],
                            status="open",
                        )
                    )
        except Exception as e:
            logger.error(f"Incident backlog scanning failed: {e}")

        return opportunities

    async def _scan_improvement_pipeline_health(self) -> List[ImprovementOpportunity]:
        """System improvement pipeline durumunu tarar."""
        from datetime import datetime, timedelta, timezone

        from libs.db.models.core_models import SystemImprovement
        from libs.db.session import AsyncSessionLocal
        from sqlalchemy import String, cast, func, select

        opportunities: List[ImprovementOpportunity] = []
        logger.info("Improvement pipeline sagligi taraniyor...")

        try:
            async with AsyncSessionLocal() as session:
                now = datetime.now(timezone.utc)
                since = now - timedelta(days=3)
                status_expr = func.lower(cast(SystemImprovement.status, String))

                grouped_stmt = (
                    select(
                        status_expr.label("status_lower"),
                        func.count(SystemImprovement.id).label("item_count"),
                        func.min(SystemImprovement.created_at).label("oldest_item"),
                    )
                    .where(SystemImprovement.created_at >= since)
                    .group_by(status_expr)
                )
                grouped_rows = (await session.execute(grouped_stmt)).all()

                counts: Dict[str, int] = {}
                oldest: Dict[str, Any] = {}
                for row in grouped_rows:
                    status_lower, item_count, oldest_item = row
                    if not status_lower:
                        continue
                    counts[str(status_lower)] = int(item_count or 0)
                    oldest[str(status_lower)] = oldest_item

                pending_count = counts.get("pending", 0)
                approved_count = counts.get("approved", 0)
                failed_count = counts.get("failed", 0) + counts.get("rejected", 0)

                if pending_count >= 6:
                    pending_age_min = (
                        int((now - oldest.get("pending")).total_seconds() / 60.0)
                        if oldest.get("pending")
                        else 0
                    )
                    opportunities.append(
                        ImprovementOpportunity(
                            id=uuid.uuid4(),
                            source_type="improvement_pipeline",
                            source_ref="pending_backlog",
                            title="Improvement proposals are piling up in pending state",
                            description=(
                                f"{pending_count} patch onerisi pending durumda bekliyor "
                                f"(en eski: {pending_age_min} dakika)."
                            ),
                            severity="high" if pending_count >= 12 else "medium",
                            category="automation",
                            evidence_detail=f"pending={pending_count} oldest_pending_min={pending_age_min}",
                            pattern_hash=ImprovementOpportunity.generate_hash(
                                "improvement_pipeline", "pending_backlog"
                            ),
                            affected_files=[
                                "services/repair/application/self_improvement_coordinator.py",
                                "apps/refine_control_plane/src/app/improvements/page.tsx",
                            ],
                            status="open",
                        )
                    )

                if approved_count >= 3:
                    approved_age_min = (
                        int((now - oldest.get("approved")).total_seconds() / 60.0)
                        if oldest.get("approved")
                        else 0
                    )
                    opportunities.append(
                        ImprovementOpportunity(
                            id=uuid.uuid4(),
                            source_type="improvement_pipeline",
                            source_ref="approved_not_applied",
                            title="Approved improvements are not being applied quickly",
                            description=(
                                f"{approved_count} patch approved durumda; effector uygulanmasi gecikiyor olabilir."
                            ),
                            severity="high",
                            category="automation",
                            evidence_detail=f"approved={approved_count} oldest_approved_min={approved_age_min}",
                            pattern_hash=ImprovementOpportunity.generate_hash(
                                "improvement_pipeline", "approved_not_applied"
                            ),
                            affected_files=[
                                "services/repair/application/self_improvement_coordinator.py",
                                "services/workflow_api/governance_router.py",
                            ],
                            status="open",
                        )
                    )

                if failed_count >= 8:
                    opportunities.append(
                        ImprovementOpportunity(
                            id=uuid.uuid4(),
                            source_type="improvement_pipeline",
                            source_ref="high_rejection_or_failure",
                            title="Patch quality drift: high reject/failed ratio",
                            description=(
                                f"Son donemde {failed_count} adet rejected/failed patch goruldu. "
                                "Oncesi dogrulama ve patch kalite bariyerleri guclendirilmeli."
                            ),
                            severity="high" if failed_count >= 16 else "medium",
                            category="quality",
                            evidence_detail=f"failed_or_rejected={failed_count}",
                            pattern_hash=ImprovementOpportunity.generate_hash(
                                "improvement_pipeline", "high_rejection_or_failure"
                            ),
                            affected_files=[
                                "services/repair/application/self_improvement_coordinator.py",
                                "services/orchestration/application/shadow_runner.py",
                            ],
                            status="open",
                        )
                    )
        except Exception as e:
            logger.error(f"Improvement pipeline scanning failed: {e}")

        return opportunities

    async def _scan_llm_provider_pressure(self) -> List[ImprovementOpportunity]:
        """LLM provider tarafında 429/402/auth baskısını tarar."""
        from datetime import datetime, timedelta, timezone

        from libs.db.models.core_models import LLMCostLog
        from libs.db.session import AsyncSessionLocal
        from sqlalchemy import String, case, cast, func, select

        opportunities: List[ImprovementOpportunity] = []
        logger.info("LLM provider pressure taramasi yapiliyor...")

        try:
            async with AsyncSessionLocal() as session:
                since = datetime.now(timezone.utc) - timedelta(hours=6)
                err_expr = func.lower(cast(LLMCostLog.error_type, String))

                err_bucket = case(
                    (err_expr.like("%429%"), "rate_limit"),
                    (err_expr.like("%rate limit%"), "rate_limit"),
                    (err_expr.like("%402%"), "billing"),
                    (err_expr.like("%payment%"), "billing"),
                    (err_expr.like("%401%"), "auth"),
                    (err_expr.like("%403%"), "auth"),
                    (err_expr.like("%auth%"), "auth"),
                    else_="other",
                ).label("err_bucket")

                stmt = (
                    select(
                        LLMCostLog.provider,
                        err_bucket,
                        func.count(LLMCostLog.id).label("fail_count"),
                    )
                    .where(LLMCostLog.created_at >= since)
                    .where((LLMCostLog.success == False) | (func.length(err_expr) > 0))
                    .group_by(LLMCostLog.provider, err_bucket)
                )
                rows = (await session.execute(stmt)).all()

                for row in rows:
                    provider, bucket, fail_count = row
                    fail_count = int(fail_count or 0)
                    if fail_count < 4:
                        continue

                    if bucket == "rate_limit":
                        category = "capacity"
                        title = f"Provider rate-limit pressure ({provider})"
                        severity = "high" if fail_count >= 12 else "medium"
                    elif bucket == "billing":
                        category = "billing"
                        title = f"Provider billing / quota issue ({provider})"
                        severity = "critical"
                    elif bucket == "auth":
                        category = "authentication"
                        title = f"Provider auth failures detected ({provider})"
                        severity = "high"
                    else:
                        category = "reliability"
                        title = f"Provider error pressure ({provider})"
                        severity = "medium"

                    opportunities.append(
                        ImprovementOpportunity(
                            id=uuid.uuid4(),
                            source_type="llm_provider_pressure",
                            source_ref=f"{provider}:{bucket}",
                            title=title,
                            description=(
                                f"{provider} icin son 6 saatte {fail_count} adet {bucket} kaynakli hata goruldu."
                            ),
                            severity=severity,
                            category=category,
                            evidence_detail=f"provider={provider} bucket={bucket} fail_count={fail_count}",
                            pattern_hash=ImprovementOpportunity.generate_hash(
                                "llm_provider_pressure", f"{provider}:{bucket}"
                            ),
                            affected_files=[
                                "libs/llm/model_orchestrator.py",
                                "services/repair/domain/root_cause.py",
                            ],
                            status="open",
                        )
                    )
        except Exception as e:
            logger.error(f"LLM provider pressure scanning failed: {e}")

        return opportunities


observer = ImprovementObserver()
