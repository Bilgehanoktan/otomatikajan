"""
Kalıcı Görev Deposu (Repository Pattern)
• Proje + alt görev CRUD
• Status geçişleri, maliyet yazma
• Yeniden başlatma sonrası veri korunur
• Faz 4: TaskLog, ApiMetric, TelegramUser, task yönetim işlemleri
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, update, func, desc, Integer
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import (
    Project, SubTask, LLMCostLog, DomainEventLog,
    TaskLog, ApiMetric, TelegramUser, TelegramCommandLog,
    ProjectStatus, SkillExecutionLog,
)


def _utcnow():
    return datetime.now(timezone.utc)


# ════════════════════════════════════════════════════════
# Proje Repository
# ════════════════════════════════════════════════════════
class ProjectRepository:

    @staticmethod
    async def create(
        db: AsyncSession,
        title: str,
        description: str,
        owner_id=None,
        job_id: str = "",
        source: str = "api",
        priority: str = "medium",
        tags: list | None = None,
        deadline=None,
        assigned_agent: str = "",
        notes: str = "",
        budget_limit: float = 0.0,
        workflow_template: str = "default",
        quality_profile: str = "standard",
        acceptance_criteria: list | None = None,
        execution_context: dict | None = None,
        review_required: bool = False,
        status: str = ProjectStatus.PENDING.value,
    ) -> Project:
        project = Project(
            id=uuid.uuid4(),
            title=title,
            description=description,
            owner_id=owner_id,
            job_id=job_id,
            status=status,
            source=source,
            priority=priority,
            tags=tags or [],
            deadline=deadline,
            assigned_agent=assigned_agent,
            notes=notes,
            budget_limit=budget_limit,
            workflow_template=workflow_template,
            quality_profile=quality_profile,
            acceptance_criteria=acceptance_criteria or [],
            execution_context=execution_context or {},
            review_required=review_required,
        )
        db.add(project)
        await db.flush()
        return project

    @staticmethod
    async def get(db: AsyncSession, project_id) -> Optional[Project]:
        result = await db.execute(
            select(Project).where(Project.id == project_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_job_id(db: AsyncSession, job_id: str) -> Optional[Project]:
        if not job_id:
            return None
        result = await db.execute(
            select(Project).where(Project.job_id == job_id)
        )
        return result.scalars().first()

    @staticmethod
    async def list_recent(
        db: AsyncSession,
        limit: int = 50,
        offset: int = 0,
        status: str | None = None,
        source: str | None = None,
        priority: str | None = None,
        search: str | None = None,
    ) -> list[Project]:
        q = select(Project).order_by(Project.created_at.desc())
        if status:
            q = q.where(Project.status == status)
        if source:
            q = q.where(Project.source == source)
        if priority:
            q = q.where(Project.priority == priority)
        if search:
            q = q.where(Project.title.ilike(f"%{search}%"))
        q = q.offset(offset).limit(limit)
        result = await db.execute(q)
        return list(result.scalars().all())

    @staticmethod
    async def mark_started(db: AsyncSession, project_id) -> None:
        await db.execute(
            update(Project)
            .where(Project.id == project_id)
            .values(status=ProjectStatus.RUNNING.value, started_at=_utcnow(), error_detail="")
        )

    @staticmethod
    async def mark_completed(
        db: AsyncSession,
        project_id,
        report: str,
        status: str = ProjectStatus.COMPLETED.value,
        total_cost: float = 0.0,
    ) -> None:
        await db.execute(
            update(Project)
            .where(Project.id == project_id)
            .values(
                status=status,
                report=report,
                total_cost=total_cost,
                progress_pct=100 if status in (ProjectStatus.COMPLETED.value, ProjectStatus.PARTIAL_COMPLETE.value) else 0,
                completed_at=_utcnow(),
            )
        )

    @staticmethod
    async def update_progress(db: AsyncSession, project_id, pct: int) -> None:
        await db.execute(
            update(Project)
            .where(Project.id == project_id)
            .values(progress_pct=max(0, min(100, pct)))
        )

    @staticmethod
    async def cancel(db: AsyncSession, project_id, cancelled_by: str = "system") -> None:
        await db.execute(
            update(Project)
            .where(Project.id == project_id)
            .values(
                status=ProjectStatus.CANCELLED.value,
                cancelled_at=_utcnow(),
                cancelled_by=cancelled_by,
            )
        )

    @staticmethod
    async def update_fields(db: AsyncSession, project_id, **fields) -> None:
        """Genel güncelleme — sadece izinli alanlar."""
        allowed = {
            "title", "description", "priority", "tags",
            "deadline", "assigned_agent", "notes", "status",
            "job_id", "progress_pct", "error_detail", "retry_count",
            "workflow_template", "quality_profile",
            "acceptance_criteria", "execution_context", "review_required",
            "cancelled_at", "cancelled_by",
            "ceo_status", "stuck_reason", "next_action", "last_supervised_at",
            "updated_at",
        }
        safe = {k: v for k, v in fields.items() if k in allowed}
        if safe:
            await db.execute(
                update(Project).where(Project.id == project_id).values(**safe)
            )

    @staticmethod
    async def update_context(db: AsyncSession, project_id, context: dict) -> None:
        """Proje execution_context'ini atomik olarak günceller."""
        # Mevcut context'i al
        p = await ProjectRepository.get(db, project_id)
        if not p: return
        
        current = p.execution_context or {}
        current.update(context)
        
        await db.execute(
            update(Project)
            .where(Project.id == project_id)
            .values(execution_context=current, updated_at=_utcnow())
        )
        await db.commit()

    @staticmethod
    async def set_error(db: AsyncSession, project_id, error: str) -> None:
        await db.execute(
            update(Project)
            .where(Project.id == project_id)
            .values(error_detail=error, status=ProjectStatus.ERROR.value)
        )

    @staticmethod
    async def increment_retry(db: AsyncSession, project_id) -> None:
        await db.execute(
            update(Project)
            .where(Project.id == project_id)
            .values(
                retry_count=Project.retry_count + 1,
                status=ProjectStatus.PENDING.value,
                error_detail="",
            )
        )

    @staticmethod
    async def set_job_id(db: AsyncSession, project_id, job_id: str) -> None:
        await db.execute(
            update(Project).where(Project.id == project_id).values(job_id=job_id)
        )

    @staticmethod
    async def mark_queued(db: AsyncSession, project_id, job_id: str) -> None:
        await db.execute(
            update(Project)
            .where(Project.id == project_id)
            .values(
                job_id=job_id,
                status=ProjectStatus.QUEUED.value,
            )
        )

    @staticmethod
    async def counts_by_status(db: AsyncSession) -> dict[str, int]:
        result = await db.execute(
            select(Project.status, func.count(Project.id))
            .group_by(Project.status)
        )
        # SRE: Ensure all keys are UPPERCASE for consistent API response mapping
        counts = {}
        for row in result.all():
            status_val = row[0]
            if status_val is None: continue
            
            # Handle both enum values and raw strings
            key = str(status_val.value if hasattr(status_val, 'value') else status_val).upper()
            counts[key] = counts.get(key, 0) + row[1]
        return counts

    @staticmethod
    async def get_total_cost(db: AsyncSession) -> float:
        """Tüm alt görevlerden toplam harcanan maliyet (USD)."""
        result = await db.execute(select(func.sum(SubTask.cost_usd)))
        return float(result.scalar() or 0.0)


# ════════════════════════════════════════════════════════
# SubTask Repository
# ════════════════════════════════════════════════════════
class SubTaskRepository:

    @staticmethod
    async def bulk_create(
        db: AsyncSession,
        project_id,
        subtask_specs: list[dict],
    ) -> list[SubTask]:
        subtasks = [
            SubTask(
                id=uuid.uuid4(),
                project_id=project_id,
                agent_id=spec["agent_id"],
                prompt=spec["prompt"],
                status=ProjectStatus.PENDING.value,
            )
            for spec in subtask_specs
        ]
        db.add_all(subtasks)
        await db.flush()
        return subtasks

    @staticmethod
    async def mark_running(db: AsyncSession, subtask_id, attempt: int) -> None:
        await db.execute(
            update(SubTask)
            .where(SubTask.id == subtask_id)
            .values(status=ProjectStatus.RUNNING.value, attempts=attempt)
        )

    @staticmethod
    async def mark_done(
        db: AsyncSession,
        subtask_id,
        result: str,
        provider: str = "",
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost_usd: float = 0.0,
        latency_s: float = 0.0,
        recovered: bool = False,
        quality_score: float | None = None,
        quality_detail: dict | None = None,
        reviewed: bool = False,
        review_notes: list | None = None,
    ) -> None:
        await db.execute(
            update(SubTask)
            .where(SubTask.id == subtask_id)
            .values(
                status=ProjectStatus.COMPLETED.value,
                result=result,
                llm_provider=provider,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost_usd,
                latency_s=latency_s,
                recovered=recovered,
                quality_score=quality_score,
                quality_detail=quality_detail or {},
                reviewed=reviewed,
                review_notes=review_notes or [],
                completed_at=_utcnow(),
            )
        )

    @staticmethod
    async def mark_failed(
        db: AsyncSession,
        subtask_id,
        result: str,
        attempts: int,
        quality_detail: dict | None = None,
    ) -> None:
        await db.execute(
            update(SubTask)
            .where(SubTask.id == subtask_id)
            .values(
                status=ProjectStatus.ERROR.value,
                result=result,
                attempts=attempts,
                quality_detail=quality_detail or {},
                completed_at=_utcnow(),
            )
        )

    @staticmethod
    async def get_by_project(db: AsyncSession, project_id, offset: int = 0, limit: int = 100) -> list[SubTask]:
        result = await db.execute(
            select(SubTask).where(SubTask.project_id == project_id)
            .order_by(SubTask.created_at)
            .offset(offset).limit(limit)
        )
        return list(result.scalars().all())


# ════════════════════════════════════════════════════════
# LLM Maliyet Repository
# ════════════════════════════════════════════════════════
class CostRepository:

    @staticmethod
    async def write(
        db: AsyncSession,
        provider: str,
        model: str,
        agent_id: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        latency_s: float,
        success: bool = True,
        error_type: str = "",
        project_id=None,
    ) -> LLMCostLog:
        log = LLMCostLog(
            provider=provider,
            model=model,
            agent_id=agent_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            latency_s=latency_s,
            success=success,
            error_type=error_type,
            project_id=project_id,
        )
        db.add(log)
        await db.flush()
        return log

    @staticmethod
    async def total_cost(db: AsyncSession) -> float:
        result = await db.execute(
            select(func.coalesce(func.sum(LLMCostLog.cost_usd), 0.0))
        )
        return float(result.scalar() or 0.0)

    @staticmethod
    async def by_provider(db: AsyncSession) -> dict[str, float]:
        result = await db.execute(
            select(LLMCostLog.provider, func.sum(LLMCostLog.cost_usd))
            .group_by(LLMCostLog.provider)
        )
        return {row[0]: round(float(row[1]), 6) for row in result.all()}


# ════════════════════════════════════════════════════════
# Domain Event Log Repository (audit trail)
# ════════════════════════════════════════════════════════
class EventLogRepository:

    @staticmethod
    async def write(
        db: AsyncSession,
        event_type: str,
        agent_id: str = "system",
        severity: str = "info",
        phase: str = "",
        message: str = "",
        payload: dict | None = None,
    ) -> None:
        log = DomainEventLog(
            event_type=event_type,
            agent_id=agent_id,
            severity=severity,
            phase=phase,
            message=message,
            payload=payload or {},
        )
        db.add(log)

    @staticmethod
    async def recent(db: AsyncSession, n: int = 100) -> list[DomainEventLog]:
        result = await db.execute(
            select(DomainEventLog)
            .order_by(DomainEventLog.created_at.desc())
            .limit(n)
        )
        return list(result.scalars().all())


# ════════════════════════════════════════════════════════
# TaskLog Repository (Faz 4)
# ════════════════════════════════════════════════════════
class TaskLogRepository:

    @staticmethod
    async def write(
        db: AsyncSession,
        project_id,
        event: str,
        message: str,
        level: str = "info",
        agent_id: str = "system",
        payload: dict | None = None,
    ) -> TaskLog:
        log = TaskLog(
            project_id=project_id,
            event=event,
            message=message,
            level=level,
            agent_id=agent_id,
            payload=payload or {},
        )
        db.add(log)
        await db.flush()
        return log

    @staticmethod
    async def get_by_project(
        db: AsyncSession,
        project_id,
        offset: int = 0,
        limit: int = 100,
    ) -> list[TaskLog]:
        result = await db.execute(
            select(TaskLog)
            .where(TaskLog.project_id == project_id)
            .order_by(TaskLog.created_at.desc())
            .offset(offset).limit(limit)
        )
        return list(result.scalars().all())


# ════════════════════════════════════════════════════════
# ApiMetric Repository (Faz 4 — Monitoring)
# ════════════════════════════════════════════════════════
class ApiMetricRepository:

    @staticmethod
    async def write(
        db: AsyncSession,
        endpoint: str,
        method: str,
        status_code: int,
        response_ms: float,
        user_id=None,
        ip_address: str = "",
        trace_id: str = "",
        error_type: str = "",
    ) -> None:
        record = ApiMetric(
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_ms=response_ms,
            user_id=user_id,
            ip_address=ip_address,
            trace_id=trace_id,
            error_type=error_type,
        )
        db.add(record)

    @staticmethod
    async def endpoint_stats(
        db: AsyncSession,
        hours: int = 24,
    ) -> list[dict]:
        """Son N saatte endpoint bazlı istatistikler."""
        from datetime import timedelta
        cutoff = _utcnow() - timedelta(hours=hours)
        result = await db.execute(
            select(
                ApiMetric.endpoint,
                ApiMetric.method,
                func.count(ApiMetric.id).label("total"),
                func.avg(ApiMetric.response_ms).label("avg_ms"),
                func.max(ApiMetric.response_ms).label("max_ms"),
                func.sum(
                    func.cast(ApiMetric.status_code >= 400, Integer)
                ).label("errors"),
            )
            .where(ApiMetric.created_at >= cutoff)
            .group_by(ApiMetric.endpoint, ApiMetric.method)
            .order_by(desc("total"))
            .limit(50)
        )
        rows = result.all()
        return [
            {
                "endpoint":  r[0],
                "method":    r[1],
                "total":     r[2],
                "avg_ms":    round(float(r[3] or 0), 1),
                "max_ms":    round(float(r[4] or 0), 1),
                "errors":    int(r[5] or 0),
                "error_rate": round(int(r[5] or 0) / r[2] * 100, 1) if r[2] else 0,
            }
            for r in rows
        ]

    @staticmethod
    async def time_series(
        db: AsyncSession,
        hours: int = 6,
        bucket_minutes: int = 5,
    ) -> list[dict]:
        """Zaman bazlı trafik serisi (bucket başına istek sayısı)."""
        from datetime import timedelta
        from sqlalchemy import text
        cutoff = _utcnow() - timedelta(hours=hours)
        sql = text("""
            SELECT
                date_trunc('minute', created_at) +
                    (EXTRACT(minute FROM created_at)::int / :bucket * :bucket || ' minutes')::interval AS bucket,
                COUNT(*) AS total,
                AVG(response_ms) AS avg_ms,
                SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) AS errors
            FROM api_metrics
            WHERE created_at >= :cutoff
            GROUP BY 1
            ORDER BY 1
        """)
        result = await db.execute(sql, {"cutoff": cutoff, "bucket": bucket_minutes})
        rows = result.all()
        return [
            {
                "bucket":  row[0].isoformat() if row[0] else None,
                "total":   int(row[1]),
                "avg_ms":  round(float(row[2] or 0), 1),
                "errors":  int(row[3] or 0),
            }
            for row in rows
        ]

    @staticmethod
    async def cleanup_old(db: AsyncSession, days: int = 7) -> int:
        """Eski kayıtları temizle."""
        from datetime import timedelta
        from sqlalchemy import delete
        cutoff = _utcnow() - timedelta(days=days)
        result = await db.execute(
            delete(ApiMetric).where(ApiMetric.created_at < cutoff)
        )
        return result.rowcount


# ════════════════════════════════════════════════════════
# Telegram Repository (Faz 4)
# ════════════════════════════════════════════════════════
class TelegramRepository:

    @staticmethod
    async def get_user(db: AsyncSession, telegram_id: str) -> Optional[TelegramUser]:
        result = await db.execute(
            select(TelegramUser).where(TelegramUser.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def upsert_user(
        db: AsyncSession,
        telegram_id: str,
        username: str = "",
        full_name: str = "",
    ) -> TelegramUser:
        user = await TelegramRepository.get_user(db, telegram_id)
        if user:
            user.username = username or user.username
            user.full_name = full_name or user.full_name
            user.last_seen_at = _utcnow()
            user.command_count += 1
        else:
            user = TelegramUser(
                telegram_id=telegram_id,
                username=username,
                full_name=full_name,
                is_authorized=False,
                last_seen_at=_utcnow(),
            )
            db.add(user)
        await db.flush()
        return user

    @staticmethod
    async def is_authorized(db: AsyncSession, telegram_id: str) -> bool:
        user = await TelegramRepository.get_user(db, telegram_id)
        return user is not None and user.is_authorized

    @staticmethod
    async def authorize(db: AsyncSession, telegram_id: str, is_admin: bool = False) -> bool:
        result = await db.execute(
            update(TelegramUser)
            .where(TelegramUser.telegram_id == telegram_id)
            .values(is_authorized=True, is_admin=is_admin)
        )
        return result.rowcount > 0

    @staticmethod
    async def list_users(db: AsyncSession) -> list[TelegramUser]:
        result = await db.execute(
            select(TelegramUser).order_by(TelegramUser.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def log_command(
        db: AsyncSession,
        telegram_id: str,
        command: str,
        arguments: str = "",
        response: str = "",
        success: bool = True,
        project_id=None,
    ) -> None:
        log = TelegramCommandLog(
            telegram_id=telegram_id,
            command=command,
            arguments=arguments,
            response=response[:2000],  # truncate
            success=success,
            project_id=project_id,
        )
        db.add(log)

# ════════════════════════════════════════════════════════
# CEO / İyileştirme Repository (Faz 8)
# ════════════════════════════════════════════════════════
from db.models import ImprovementOpportunity, CEOSuggestedTask

class ImprovementRepository:

    @staticmethod
    async def create(
        db: AsyncSession,
        title: str,
        description: str,
        source_type: str = "visual_audit",
        severity: str = "medium",
        category: str = "ux_ui",
        impact_score: float = 0.5,
        evidence: str = "",
    ) -> ImprovementOpportunity:
        # Tekrar önlemek için hash oluştur
        pattern_hash = ImprovementOpportunity.generate_hash(source_type, title[:50])
        
        opp = ImprovementOpportunity(
            id=uuid.uuid4(),
            title=title,
            description=description,
            source_type=source_type,
            severity=severity,
            category=category,
            impact_score=impact_score,
            evidence_detail=evidence,
            pattern_hash=pattern_hash,
            status="open"
        )
        db.add(opp)
        await db.flush()
        return opp

    @staticmethod
    async def list_open(db: AsyncSession, limit: int = 20) -> list[ImprovementOpportunity]:
        result = await db.execute(
            select(ImprovementOpportunity)
            .where(ImprovementOpportunity.status == "open")
            .order_by(ImprovementOpportunity.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def mark_resolved(db: AsyncSession, opp_id: uuid.UUID) -> None:
        await db.execute(
            update(ImprovementOpportunity)
            .where(ImprovementOpportunity.id == opp_id)
            .values(status="resolved")
        )


# ════════════════════════════════════════════════════════
# Skill Execution Log Repository (Faz 13)
# ════════════════════════════════════════════════════════
class SkillLogRepository:

    @staticmethod
    async def write(
        db: AsyncSession,
        project_id: uuid.UUID,
        skill_id: str,
        agent_id: str = "system",
        success: bool = True,
        summary: str = "",
        data: dict | None = None,
        duration_s: float = 0.0,
    ) -> SkillExecutionLog:
        log = SkillExecutionLog(
            project_id=project_id,
            skill_id=skill_id,
            agent_id=agent_id,
            success=success,
            summary=summary,
            data=data or {},
            duration_s=duration_s,
        )
        db.add(log)
        await db.flush()
        return log

    @staticmethod
    async def get_by_project(
        db: AsyncSession,
        project_id: uuid.UUID,
        limit: int = 100,
    ) -> list[SkillExecutionLog]:
        result = await db.execute(
            select(SkillExecutionLog)
            .where(SkillExecutionLog.project_id == project_id)
            .order_by(SkillExecutionLog.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())
