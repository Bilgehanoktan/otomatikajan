import uuid
from datetime import UTC, datetime

from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from libs.db.models.governance_models import (
    GovernorAlertRecord,
    GovernorAlertSeverity,
    GovernorAlertStatus,
    GovernorAlertType,
    GovernorDomain,
    GovernorDriftRecord,
    GovernorDriftType,
    GovernorMetricAggregateRecord,
)


class GovernorAlertRepo:
    @staticmethod
    async def create_alert(
        db: AsyncSession,
        alert_type: GovernorAlertType,
        severity: GovernorAlertSeverity,
        title: str,
        summary: str | None = None,
        domain: GovernorDomain | None = None,
        metric_value: float | None = None,
        threshold_value: float | None = None,
        evidence_payload: dict | None = None
    ) -> GovernorAlertRecord:
        record = GovernorAlertRecord(
            alert_type=alert_type,
            severity=severity,
            status=GovernorAlertStatus.OPEN,
            title=title,
            summary=summary,
            domain=domain,
            metric_value=metric_value,
            threshold_value=threshold_value,
            evidence_payload=evidence_payload
        )
        db.add(record)
        return record

    @staticmethod
    async def list_open_alerts(db: AsyncSession, limit: int = 50) -> list[GovernorAlertRecord]:
        stmt = select(GovernorAlertRecord).where(GovernorAlertRecord.status == GovernorAlertStatus.OPEN).order_by(desc(GovernorAlertRecord.opened_at))
        res = await db.execute(stmt.limit(limit))
        return list(res.scalars().all())

    @staticmethod
    async def update_status(db: AsyncSession, alert_id: uuid.UUID, status: GovernorAlertStatus, owner_id: str | None = None) -> bool:
        values = {"status": status}
        if status == GovernorAlertStatus.ACKNOWLEDGED:
            values["acknowledged_at"] = datetime.now(UTC)
            if owner_id: values["owner_id"] = owner_id
        elif status == GovernorAlertStatus.RESOLVED:
            values["resolved_at"] = datetime.now(UTC)

        stmt = update(GovernorAlertRecord).where(GovernorAlertRecord.id == alert_id).values(**values)
        await db.execute(stmt)
        return True


class GovernorMetricAggregateRepo:
    @staticmethod
    async def save_metric_aggregate(
        db: AsyncSession,
        metric_key: str,
        value: float,
        domain: GovernorDomain | None = None,
        window_minutes: int = 60,
        sample_size: int = 0,
        baseline_value: float | None = None
    ) -> GovernorMetricAggregateRecord:
        delta = None
        if baseline_value is not None:
            delta = value - baseline_value

        record = GovernorMetricAggregateRecord(
            metric_key=metric_key,
            domain=domain,
            value=value,
            baseline_value=baseline_value,
            delta_value=delta,
            window_minutes=window_minutes,
            sample_size=sample_size
        )
        db.add(record)
        return record

    @staticmethod
    async def get_latest_metrics(db: AsyncSession, limit: int = 20) -> list[GovernorMetricAggregateRecord]:
        res = await db.execute(select(GovernorMetricAggregateRecord).order_by(desc(GovernorMetricAggregateRecord.created_at)).limit(limit))
        return list(res.scalars().all())


class GovernorDriftRepo:
    @staticmethod
    async def save_drift_record(
        db: AsyncSession,
        drift_type: GovernorDriftType,
        domain: GovernorDomain | None,
        drift_score: float,
        summary: str,
        evidence_payload: dict | None = None
    ) -> GovernorDriftRecord:
        record = GovernorDriftRecord(
            drift_type=drift_type,
            domain=domain,
            drift_score=drift_score,
            summary=summary,
            evidence_payload=evidence_payload
        )
        db.add(record)
        return record

    @staticmethod
    async def list_recent_drifts(db: AsyncSession, limit: int = 50) -> list[GovernorDriftRecord]:
        res = await db.execute(select(GovernorDriftRecord).order_by(desc(GovernorDriftRecord.created_at)).limit(limit))
        return list(res.scalars().all())
