"""
Repair Repository — DB erişim katmanı.
Tüm repair CRUD işlemleri burada toplanır.
"""

from typing import Optional
from sqlalchemy import select, update, desc
from sqlalchemy.ext.asyncio import AsyncSession

from packages.persistence.repair_models import RepairIncident, RepairJobRecord, RepairProposal, RepairPatchLog
from packages.repair_engine.schemas.incident import IncidentRecord
from packages.repair_engine.schemas.repair_job import RepairJob
from packages.repair_engine.release.pr_creator import PRProposal
from packages.repair_engine.memory.patch_memory import PatchRecord


class RepairIncidentRepo:
    @staticmethod
    async def upsert(db: AsyncSession, incident: IncidentRecord) -> RepairIncident:
        stmt = select(RepairIncident).where(RepairIncident.incident_id == incident.incident_id)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            existing.occurrence_count = incident.occurrence_count
            existing.last_seen_at     = incident.last_seen_at
            existing.status           = incident.status
            return existing
        rec = RepairIncident(
            incident_id=incident.incident_id,
            source=incident.source.value,
            severity=incident.severity.value,
            service=incident.service,
            module=incident.module,
            symptom=incident.symptom[:1000],
            stack_trace=incident.stack_trace[:5000],
            suspected_files=incident.suspected_files,
            failing_tests=incident.failing_tests,
            reproduction_hint=incident.reproduction_hint[:500],
            context_data=incident.context,
            occurrence_count=incident.occurrence_count,
            status=incident.status,
            first_seen_at=incident.first_seen_at,
            last_seen_at=incident.last_seen_at,
        )
        db.add(rec)
        return rec

    @staticmethod
    async def get_open(db: AsyncSession, limit: int = 50) -> list[RepairIncident]:
        stmt = (
            select(RepairIncident)
            .where(RepairIncident.status == "open")
            .order_by(desc(RepairIncident.last_seen_at))
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def mark_resolved(db: AsyncSession, incident_id: str) -> bool:
        stmt = (
            update(RepairIncident)
            .where(RepairIncident.incident_id == incident_id)
            .values(status="resolved")
        )
        result = await db.execute(stmt)
        return result.rowcount > 0


class RepairJobRepo:
    @staticmethod
    async def upsert(db: AsyncSession, job: RepairJob) -> RepairJobRecord:
        # Faz 12+ alanlarını meta içine paketle
        meta_data = {
            "canary_id": job.canary_id,
            "canary_status": job.canary_status,
            "generated_tests": job.generated_tests,
            "fingerprint_hash": job.fingerprint_hash,
            "duplicate_of": job.duplicate_of,
            "risk_score": job.risk_score,
            "vector_context_used": job.vector_context_used,
            "vector_context_summary": job.vector_context_summary,
            "debate_triggered": job.debate_triggered,
            "debate_result_summary": job.debate_result_summary,
            "debate_winning_hypothesis": job.debate_winning_hypothesis,
            "sandbox_verified": job.sandbox_verified,
            "lesson_saved": job.lesson_saved,
            "ranker_adjusted": job.ranker_adjusted,
            "ranker_adjusted_confidence": job.ranker_adjusted_confidence,
        }

        stmt = select(RepairJobRecord).where(RepairJobRecord.job_id == job.job_id)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            existing.status        = job.status.value
            existing.ticket_id     = job.ticket_id
            existing.plan_id       = job.plan_id
            existing.validation_id = job.validation_id
            existing.pr_url        = job.pr_url
            existing.branch_name   = job.branch_name
            existing.diff          = job.diff[:20000] # Diff limit arttırıldı
            existing.error_detail  = job.error_detail[:2000]
            existing.history       = job.history
            existing.meta          = meta_data
            existing.updated_at    = job.updated_at
            return existing

        rec = RepairJobRecord(
            job_id=job.job_id,
            incident_id=job.incident_id,
            status=job.status.value,
            history=job.history,
            meta=meta_data,
            created_at=job.created_at,
        )
        db.add(rec)
        return rec

    @staticmethod
    async def list_recent(db: AsyncSession, limit: int = 20) -> list[RepairJobRecord]:
        stmt = (
            select(RepairJobRecord)
            .order_by(desc(RepairJobRecord.created_at))
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get(db: AsyncSession, job_id: str) -> Optional[RepairJobRecord]:
        stmt = select(RepairJobRecord).where(RepairJobRecord.job_id == job_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def find_zombies(db: AsyncSession, threshold_hours: int = 1) -> list[RepairJobRecord]:
        """Kilitlenmiş (zombi) işleri (Running/Pending) bul."""
        from datetime import datetime, timezone, timedelta
        limit = datetime.now(timezone.utc) - timedelta(hours=threshold_hours)
        stmt = (
            select(RepairJobRecord)
            .where(RepairJobRecord.status.in_(["running", "pending"]))
            .where(RepairJobRecord.created_at < limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def bulk_fail(db: AsyncSession, job_ids: list[str], reason: str) -> int:
        """Birden fazla işi toplu olarak FAILED durumuna çek."""
        if not job_ids: return 0
        from datetime import datetime, timezone
        stmt = (
            update(RepairJobRecord)
            .where(RepairJobRecord.job_id.in_(job_ids))
            .values(
                status="failed",
                error_detail=reason[:2000],
                updated_at=datetime.now(timezone.utc)
            )
        )
        result = await db.execute(stmt)
        return result.rowcount


class RepairProposalRepo:
    @staticmethod
    async def save(db: AsyncSession, proposal: PRProposal) -> RepairProposal:
        rec = RepairProposal(
            pr_id=proposal.pr_id,
            job_id=proposal.job_id,
            incident_id=proposal.incident_id,   # Faz 10.1 düzeltme: job_id değil incident_id
            branch_name=proposal.branch_name,
            title=proposal.title[:500],
            body=proposal.body[:10000],
            diff=proposal.diff[:20000],
            changed_files=proposal.changed_files,
            risk_level=proposal.risk_level,
            validation_summary=proposal.validation_summary[:500],
            auto_merge=False,
        )
        db.add(rec)
        return rec

    @staticmethod
    async def list_pending(db: AsyncSession) -> list[RepairProposal]:
        stmt = (
            select(RepairProposal)
            .where(RepairProposal.decision == "pending")
            .order_by(desc(RepairProposal.created_at))
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def decide(db: AsyncSession, pr_id: str, decision: str, decided_by: str = "human") -> bool:
        from datetime import datetime, timezone
        stmt = (
            update(RepairProposal)
            .where(RepairProposal.pr_id == pr_id)
            .values(
                decision=decision,
                decided_by=decided_by,
                decided_at=datetime.now(timezone.utc),
            )
        )
        result = await db.execute(stmt)
        return result.rowcount > 0


class RepairPatchLogRepo:
    @staticmethod
    async def save(db: AsyncSession, record: PatchRecord) -> RepairPatchLog:
        rec = RepairPatchLog(
            record_id=record.record_id,
            job_id=record.job_id,
            incident_id=record.incident_id,
            classification=record.classification,
            target_files=record.target_files,
            diff_size_lines=record.diff_size_lines,
            outcome=record.outcome.value,
            confidence=record.confidence,
            validation_score=record.validation_score,
            notes=record.notes[:500],
            recorded_at=record.recorded_at,
        )
        db.add(rec)
        return rec

    @staticmethod
    async def success_rate(db: AsyncSession, classification: str) -> float:
        """DB'den başarı oranı hesapla."""
        stmt = select(RepairPatchLog).where(RepairPatchLog.classification == classification)
        result = await db.execute(stmt)
        records = list(result.scalars().all())
        if not records:
            return 0.5
        success = sum(1 for r in records if r.outcome in ("success", "manual_merged"))
        return round(success / len(records), 2)
