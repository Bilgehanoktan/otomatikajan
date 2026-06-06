from datetime import datetime, timezone
import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from apps.bilgeapi.repositories.interface import (
    IncidentRepository, DiagnosticRepository, FindingRepository,
    RecommendationRepository, RepairRequestRepository, AuditRepository, WebhookDeliveryRepository,
    ReleaseCheckRepository, ApiKeyRepository
)
from apps.bilgeapi.schemas.incident import IncidentCreate, IncidentResponse
from apps.bilgeapi.schemas.diagnostic import DiagnosticResult, DiagnosticStatus
from apps.bilgeapi.schemas.repair import RepairRequestCreate, RepairRequestResponse, ApprovalStatus, DispatchStatus
from apps.bilgeapi.schemas.audit import AuditEvent
from apps.bilgeapi.models.database import (
    IncidentModel, DiagnosticRunModel, FindingModel, RecommendationModel,
    RepairRequestModel, AuditEventModel, WebhookDeliveryModel, ReleaseCheckModel,
    ApiKeyModel
)

class PostgresIncidentRepository(IncidentRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, incident: IncidentCreate) -> IncidentResponse:
        inc_id = f"inc_{uuid.uuid4().hex[:8]}"
        model = IncidentModel(
            id=inc_id,
            project_key=incident.project_key,
            source_system=incident.source_system,
            environment=incident.environment,
            kind=incident.kind,
            severity=incident.severity.value if hasattr(incident.severity, "value") else incident.severity,
            error_message=incident.error_message,
            stack_trace=incident.stack_trace,
            occurred_at=incident.occurred_at,
            correlation_id=incident.correlation_id,
            tags=incident.tags,
            metadata_fields=incident.metadata
        )
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        return IncidentResponse(
            id=model.id,
            created_at=model.created_at,
            project_key=model.project_key,
            source_system=model.source_system,
            environment=model.environment,
            kind=model.kind,
            severity=model.severity,
            error_message=model.error_message,
            stack_trace=model.stack_trace,
            occurred_at=model.occurred_at,
            correlation_id=model.correlation_id,
            tags=model.tags or [],
            metadata=model.metadata_fields or {}
        )

    async def get(self, incident_id: str) -> Optional[IncidentResponse]:
        res = await self.db.execute(select(IncidentModel).where(IncidentModel.id == incident_id))
        model = res.scalar_one_or_none()
        if not model:
            return None
        return IncidentResponse(
            id=model.id,
            created_at=model.created_at,
            project_key=model.project_key,
            source_system=model.source_system,
            environment=model.environment,
            kind=model.kind,
            severity=model.severity,
            error_message=model.error_message,
            stack_trace=model.stack_trace,
            occurred_at=model.occurred_at,
            correlation_id=model.correlation_id,
            tags=model.tags or [],
            metadata=model.metadata_fields or {}
        )

    async def list_all(self, project_key: Optional[str] = None) -> List[IncidentResponse]:
        query = select(IncidentModel).order_by(desc(IncidentModel.created_at))
        if project_key:
            query = query.where(IncidentModel.project_key == project_key)
        res = await self.db.execute(query)
        models = res.scalars().all()
        return [
            IncidentResponse(
                id=m.id,
                created_at=m.created_at,
                project_key=m.project_key,
                source_system=m.source_system,
                environment=m.environment,
                kind=m.kind,
                severity=m.severity,
                error_message=m.error_message,
                stack_trace=m.stack_trace,
                occurred_at=m.occurred_at,
                correlation_id=m.correlation_id,
                tags=m.tags or [],
                metadata=m.metadata_fields or {}
            )
            for m in models
        ]


class PostgresDiagnosticRepository(DiagnosticRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, incident_id: str) -> DiagnosticResult:
        diag_id = f"diag_{uuid.uuid4().hex[:8]}"
        model = DiagnosticRunModel(
            diagnostic_id=diag_id,
            incident_id=incident_id,
            status=DiagnosticStatus.QUEUED.value
        )
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        return DiagnosticResult(
            diagnostic_id=model.diagnostic_id,
            incident_id=model.incident_id,
            status=model.status,
            summary=model.summary,
            root_cause_hypothesis=model.root_cause_hypothesis,
            confidence=model.confidence,
            risk_score=model.risk_score,
            findings=[],
            recommendations=[],
            created_at=model.created_at,
            completed_at=model.completed_at
        )

    async def get(self, diagnostic_id: str) -> Optional[DiagnosticResult]:
        res = await self.db.execute(select(DiagnosticRunModel).where(DiagnosticRunModel.diagnostic_id == diagnostic_id))
        model = res.scalar_one_or_none()
        if not model:
            return None
        return DiagnosticResult(
            diagnostic_id=model.diagnostic_id,
            incident_id=model.incident_id,
            status=model.status,
            summary=model.summary,
            root_cause_hypothesis=model.root_cause_hypothesis,
            confidence=model.confidence,
            risk_score=model.risk_score,
            findings=[{"id": f.id, "diagnostic_id": f.diagnostic_id, "description": f.description, "metadata": f.metadata_fields} for f in model.findings],
            recommendations=[{"id": r.id, "diagnostic_id": r.diagnostic_id, "description": r.description, "metadata": r.metadata_fields} for r in model.recommendations],
            created_at=model.created_at,
            completed_at=model.completed_at
        )

    async def update(self, diagnostic_id: str, status: DiagnosticStatus, **kwargs) -> Optional[DiagnosticResult]:
        res = await self.db.execute(select(DiagnosticRunModel).where(DiagnosticRunModel.diagnostic_id == diagnostic_id))
        model = res.scalar_one_or_none()
        if not model:
            return None
        model.status = status.value if hasattr(status, "value") else status
        for k, v in kwargs.items():
            if k in ("findings", "recommendations"):
                continue
            setattr(model, k, v)
        if status in (DiagnosticStatus.COMPLETED, DiagnosticStatus.FAILED) and not model.completed_at:
            model.completed_at = datetime.now(timezone.utc)
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        return await self.get(diagnostic_id)

    async def list_all(self) -> List[DiagnosticResult]:
        res = await self.db.execute(select(DiagnosticRunModel).order_by(desc(DiagnosticRunModel.created_at)))
        models = res.scalars().all()
        results = []
        for model in models:
            results.append(
                DiagnosticResult(
                    diagnostic_id=model.diagnostic_id,
                    incident_id=model.incident_id,
                    status=model.status,
                    summary=model.summary,
                    root_cause_hypothesis=model.root_cause_hypothesis,
                    confidence=model.confidence,
                    risk_score=model.risk_score,
                    findings=[{"id": f.id, "diagnostic_id": f.diagnostic_id, "description": f.description, "metadata": f.metadata_fields} for f in model.findings],
                    recommendations=[{"id": r.id, "diagnostic_id": r.diagnostic_id, "description": r.description, "metadata": r.metadata_fields} for r in model.recommendations],
                    created_at=model.created_at,
                    completed_at=model.completed_at
                )
            )
        return results


class PostgresFindingRepository(FindingRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, diagnostic_id: str, finding_data: Dict[str, Any]) -> Dict[str, Any]:
        f_id = f"find_{uuid.uuid4().hex[:8]}"
        model = FindingModel(
            id=f_id,
            diagnostic_id=diagnostic_id,
            description=finding_data.get("description", ""),
            metadata_fields={k: v for k, v in finding_data.items() if k != "description"}
        )
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        return {"id": model.id, "diagnostic_id": model.diagnostic_id, "description": model.description, "metadata": model.metadata_fields}

    async def list_by_diagnostic(self, diagnostic_id: str) -> List[Dict[str, Any]]:
        res = await self.db.execute(select(FindingModel).where(FindingModel.diagnostic_id == diagnostic_id))
        models = res.scalars().all()
        return [{"id": m.id, "diagnostic_id": m.diagnostic_id, "description": m.description, "metadata": m.metadata_fields} for m in models]


class PostgresRecommendationRepository(RecommendationRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, diagnostic_id: str, recommendation_data: Dict[str, Any]) -> Dict[str, Any]:
        r_id = f"rec_{uuid.uuid4().hex[:8]}"
        model = RecommendationModel(
            id=r_id,
            diagnostic_id=diagnostic_id,
            description=recommendation_data.get("description", ""),
            metadata_fields={k: v for k, v in recommendation_data.items() if k != "description"}
        )
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        return {"id": model.id, "diagnostic_id": model.diagnostic_id, "description": model.description, "metadata": model.metadata_fields}

    async def list_by_diagnostic(self, diagnostic_id: str) -> List[Dict[str, Any]]:
        res = await self.db.execute(select(RecommendationModel).where(RecommendationModel.diagnostic_id == diagnostic_id))
        models = res.scalars().all()
        return [{"id": m.id, "diagnostic_id": m.diagnostic_id, "description": m.description, "metadata": m.metadata_fields} for m in models]


class PostgresRepairRequestRepository(RepairRequestRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, diagnostic_id: str, request: RepairRequestCreate) -> RepairRequestResponse:
        rep_id = f"rep_{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc)
        model = RepairRequestModel(
            id=rep_id,
            diagnostic_id=diagnostic_id,
            requested_by=request.requested_by,
            approval_status=request.approval_status.value if hasattr(request.approval_status, "value") else request.approval_status,
            risk_score=request.risk_score,
            risk_reason=request.risk_reason,
            dispatch_status=DispatchStatus.PENDING.value,
            approval_required=request.approval_required,
            rejection_reason=None,
            approved_by=request.approved_by,
            approved_at=request.approved_at,
            rejected_at=None,
            created_at=now,
            updated_at=now
        )
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        return RepairRequestResponse(
            id=model.id,
            diagnostic_id=model.diagnostic_id,
            requested_by=model.requested_by,
            approved_by=model.approved_by,
            approval_status=model.approval_status,
            risk_score=model.risk_score,
            risk_reason=model.risk_reason,
            dispatch_status=model.dispatch_status,
            external_reference=model.external_reference,
            approval_required=model.approval_required,
            rejection_reason=model.rejection_reason,
            approved_at=model.approved_at,
            rejected_at=model.rejected_at,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    async def get(self, repair_request_id: str) -> Optional[RepairRequestResponse]:
        res = await self.db.execute(select(RepairRequestModel).where(RepairRequestModel.id == repair_request_id))
        model = res.scalar_one_or_none()
        if not model:
            return None
        return RepairRequestResponse(
            id=model.id,
            diagnostic_id=model.diagnostic_id,
            requested_by=model.requested_by,
            approved_by=model.approved_by,
            approval_status=model.approval_status,
            risk_score=model.risk_score,
            risk_reason=model.risk_reason,
            dispatch_status=model.dispatch_status,
            external_reference=model.external_reference,
            approval_required=model.approval_required,
            rejection_reason=model.rejection_reason,
            approved_at=model.approved_at,
            rejected_at=model.rejected_at,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    async def update(self, repair_request_id: str, approval_status: ApprovalStatus, dispatch_status: DispatchStatus, **kwargs) -> Optional[RepairRequestResponse]:
        res = await self.db.execute(select(RepairRequestModel).where(RepairRequestModel.id == repair_request_id))
        model = res.scalar_one_or_none()
        if not model:
            return None
        model.approval_status = approval_status.value if hasattr(approval_status, "value") else approval_status
        model.dispatch_status = dispatch_status.value if hasattr(dispatch_status, "value") else dispatch_status
        model.updated_at = datetime.now(timezone.utc)
        for k, v in kwargs.items():
            setattr(model, k, v)
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        return await self.get(repair_request_id)

    async def list_all(self) -> List[RepairRequestResponse]:
        res = await self.db.execute(select(RepairRequestModel).order_by(desc(RepairRequestModel.created_at)))
        models = res.scalars().all()
        return [
            RepairRequestResponse(
                id=m.id,
                diagnostic_id=m.diagnostic_id,
                requested_by=m.requested_by,
                approved_by=m.approved_by,
                approval_status=m.approval_status,
                risk_score=m.risk_score,
                risk_reason=m.risk_reason,
                dispatch_status=m.dispatch_status,
                external_reference=m.external_reference,
                approval_required=m.approval_required,
                rejection_reason=m.rejection_reason,
                approved_at=m.approved_at,
                rejected_at=m.rejected_at,
                created_at=m.created_at,
                updated_at=m.updated_at
            )
            for m in models
        ]


class PostgresAuditRepository(AuditRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def write(self, event: AuditEvent) -> None:
        model = AuditEventModel(
            id=event.id,
            event_type=event.event_type,
            actor_id=event.actor_id,
            actor_type=event.actor_type,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            request_id=event.request_id,
            correlation_id=event.correlation_id,
            ip_address=event.ip_address,
            user_agent=event.user_agent,
            before_state=event.before_state,
            after_state=event.after_state,
            metadata_fields=event.metadata,
            created_at=event.created_at
        )
        self.db.add(model)
        await self.db.commit()

    async def list_recent(self, limit: int = 100) -> List[AuditEvent]:
        res = await self.db.execute(select(AuditEventModel).order_by(desc(AuditEventModel.created_at)).limit(limit))
        models = res.scalars().all()
        return [
            AuditEvent(
                id=m.id,
                event_type=m.event_type,
                actor_id=m.actor_id,
                actor_type=m.actor_type,
                entity_type=m.entity_type,
                entity_id=m.entity_id,
                request_id=m.request_id,
                correlation_id=m.correlation_id,
                ip_address=m.ip_address,
                user_agent=m.user_agent,
                before_state=m.before_state,
                after_state=m.after_state,
                metadata=m.metadata_fields or {},
                created_at=m.created_at
            )
            for m in models
        ]


class PostgresWebhookDeliveryRepository(WebhookDeliveryRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_delivery(self, delivery_data: Dict[str, Any]) -> None:
        model = WebhookDeliveryModel(
            id=f"web_{uuid.uuid4().hex[:8]}",
            repair_request_id=delivery_data.get("repair_request_id", ""),
            webhook_url=delivery_data.get("webhook_url", ""),
            status_code=delivery_data.get("status_code"),
            delivery_status=delivery_data.get("delivery_status", ""),
            error_message=delivery_data.get("error_message"),
            payload_hash=delivery_data.get("payload_hash", ""),
            attempt_count=delivery_data.get("attempt_count", 1.0)
        )
        self.db.add(model)
        await self.db.commit()

    async def create_delivery(self, delivery_data: Dict[str, Any]) -> Dict[str, Any]:
        del_id = f"web_{uuid.uuid4().hex[:8]}"
        model = WebhookDeliveryModel(
            id=del_id,
            repair_request_id=delivery_data.get("repair_request_id", ""),
            webhook_url=delivery_data.get("webhook_url", ""),
            status_code=delivery_data.get("status_code"),
            delivery_status=delivery_data.get("delivery_status", ""),
            error_message=delivery_data.get("error_message"),
            payload_hash=delivery_data.get("payload_hash", ""),
            attempt_count=delivery_data.get("attempt_count", 1.0)
        )
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        return {
            "id": model.id,
            "repair_request_id": model.repair_request_id,
            "webhook_url": model.webhook_url,
            "status_code": model.status_code,
            "delivery_status": model.delivery_status,
            "error_message": model.error_message,
            "payload_hash": model.payload_hash,
            "attempt_count": model.attempt_count,
            "created_at": model.created_at
        }

    async def update_delivery(self, delivery_id: str, delivery_status: str, status_code: Optional[float], error_message: Optional[str], attempt_count: float) -> Optional[Dict[str, Any]]:
        res = await self.db.execute(select(WebhookDeliveryModel).where(WebhookDeliveryModel.id == delivery_id))
        model = res.scalar_one_or_none()
        if not model:
            return None
        model.delivery_status = delivery_status
        model.status_code = status_code
        model.error_message = error_message
        model.attempt_count = attempt_count
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        return {
            "id": model.id,
            "repair_request_id": model.repair_request_id,
            "webhook_url": model.webhook_url,
            "status_code": model.status_code,
            "delivery_status": model.delivery_status,
            "error_message": model.error_message,
            "payload_hash": model.payload_hash,
            "attempt_count": model.attempt_count,
            "created_at": model.created_at
        }

    async def get_delivery(self, delivery_id: str) -> Optional[Dict[str, Any]]:
        res = await self.db.execute(select(WebhookDeliveryModel).where(WebhookDeliveryModel.id == delivery_id))
        model = res.scalar_one_or_none()
        if not model:
            return None
        return {
            "id": model.id,
            "repair_request_id": model.repair_request_id,
            "webhook_url": model.webhook_url,
            "status_code": model.status_code,
            "delivery_status": model.delivery_status,
            "error_message": model.error_message,
            "payload_hash": model.payload_hash,
            "attempt_count": model.attempt_count,
            "created_at": model.created_at
        }

    async def list_deliveries(self) -> List[Dict[str, Any]]:
        res = await self.db.execute(select(WebhookDeliveryModel).order_by(desc(WebhookDeliveryModel.created_at)))
        models = res.scalars().all()
        return [
            {
                "id": m.id,
                "repair_request_id": m.repair_request_id,
                "webhook_url": m.webhook_url,
                "status_code": m.status_code,
                "delivery_status": m.delivery_status,
                "error_message": m.error_message,
                "payload_hash": m.payload_hash,
                "attempt_count": m.attempt_count,
                "created_at": m.created_at
            }
            for m in models
        ]


class PostgresReleaseCheckRepository(ReleaseCheckRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    def _to_dict(self, model: ReleaseCheckModel) -> Dict[str, Any]:
        return {
            "id": model.id,
            "status": model.status,
            "score": model.score,
            "blockers": model.blockers or [],
            "warnings": model.warnings or [],
            "checked_modules": model.checked_modules or {},
            "checked_endpoints": model.checked_endpoints or {},
            "smoke_trace": model.smoke_trace or [],
            "app_version": model.app_version,
            "git_sha": model.git_sha,
            "environment": model.environment,
            "triggered_by": model.triggered_by,
            "created_at": model.created_at
        }

    async def create_check(self, check_data: Dict[str, Any]) -> Dict[str, Any]:
        check_data = check_data.copy()
        if "id" not in check_data:
            check_data["id"] = f"rel_{uuid.uuid4().hex[:8]}"
        if "created_at" not in check_data:
            check_data["created_at"] = datetime.now(timezone.utc)

        model = ReleaseCheckModel(
            id=check_data["id"],
            status=check_data["status"],
            score=check_data["score"],
            blockers=check_data.get("blockers"),
            warnings=check_data.get("warnings"),
            checked_modules=check_data.get("checked_modules"),
            checked_endpoints=check_data.get("checked_endpoints"),
            smoke_trace=check_data.get("smoke_trace"),
            app_version=check_data.get("app_version"),
            git_sha=check_data.get("git_sha"),
            environment=check_data.get("environment"),
            triggered_by=check_data.get("triggered_by"),
            created_at=check_data["created_at"]
        )
        self.db.add(model)
        await self.db.commit()
        return self._to_dict(model)

    async def get_latest_check(self) -> Optional[Dict[str, Any]]:
        res = await self.db.execute(select(ReleaseCheckModel).order_by(desc(ReleaseCheckModel.created_at)).limit(1))
        model = res.scalar_one_or_none()
        if not model:
            return None
        return self._to_dict(model)

    async def list_checks(self, limit: int = 20) -> List[Dict[str, Any]]:
        res = await self.db.execute(select(ReleaseCheckModel).order_by(desc(ReleaseCheckModel.created_at)).limit(limit))
        models = res.scalars().all()
        return [self._to_dict(m) for m in models]


class PostgresApiKeyRepository(ApiKeyRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    def _to_dict(self, model: ApiKeyModel) -> Dict[str, Any]:
        return {
            "id": model.id,
            "key_hash": model.key_hash,
            "key_prefix": model.key_prefix,
            "key_fingerprint": model.key_fingerprint,
            "role": model.role,
            "description": model.description,
            "tenant_id": model.tenant_id,
            "is_active": model.is_active,
            "created_by": model.created_by,
            "revoked_by": model.revoked_by,
            "revoke_reason": model.revoke_reason,
            "expires_at": model.expires_at,
            "created_at": model.created_at,
            "revoked_at": model.revoked_at,
            "last_used_at": model.last_used_at,
            "quota_daily": model.quota_daily,
            "quota_monthly": model.quota_monthly
        }

    async def create(self, key_data: Dict[str, Any]) -> Dict[str, Any]:
        model = ApiKeyModel(
            id=key_data.get("id") or f"key_{uuid.uuid4().hex[:8]}",
            key_hash=key_data["key_hash"],
            key_prefix=key_data["key_prefix"],
            key_fingerprint=key_data["key_fingerprint"],
            role=key_data["role"],
            description=key_data.get("description"),
            tenant_id=key_data.get("tenant_id"),
            is_active=key_data.get("is_active", True),
            created_by=key_data.get("created_by"),
            expires_at=key_data.get("expires_at"),
            created_at=key_data.get("created_at") or datetime.now(timezone.utc),
            quota_daily=key_data.get("quota_daily"),
            quota_monthly=key_data.get("quota_monthly")
        )
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        return self._to_dict(model)

    async def get(self, key_id: str) -> Optional[Dict[str, Any]]:
        res = await self.db.execute(select(ApiKeyModel).where(ApiKeyModel.id == key_id))
        model = res.scalar_one_or_none()
        if not model:
            return None
        return self._to_dict(model)

    async def get_by_hash(self, key_hash: str) -> Optional[Dict[str, Any]]:
        # High efficiency indexed lookup
        res = await self.db.execute(select(ApiKeyModel).where(ApiKeyModel.key_hash == key_hash))
        model = res.scalar_one_or_none()
        if not model:
            return None
        return self._to_dict(model)

    async def list_all(self) -> List[Dict[str, Any]]:
        res = await self.db.execute(select(ApiKeyModel).order_by(desc(ApiKeyModel.created_at)))
        models = res.scalars().all()
        return [self._to_dict(m) for m in models]

    async def revoke(self, key_id: str, revoked_by: str, reason: str) -> Optional[Dict[str, Any]]:
        res = await self.db.execute(select(ApiKeyModel).where(ApiKeyModel.id == key_id))
        model = res.scalar_one_or_none()
        if not model:
            return None
        model.is_active = False
        model.revoked_by = revoked_by
        model.revoke_reason = reason
        model.revoked_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(model)
        return self._to_dict(model)

    async def update_last_used(self, key_id: str, last_used: datetime) -> None:
        res = await self.db.execute(select(ApiKeyModel).where(ApiKeyModel.id == key_id))
        model = res.scalar_one_or_none()
        if model:
            model.last_used_at = last_used
            await self.db.commit()

    async def update_quota(self, key_id: str, quota_daily: Optional[int], quota_monthly: Optional[int]) -> Optional[Dict[str, Any]]:
        res = await self.db.execute(select(ApiKeyModel).where(ApiKeyModel.id == key_id))
        model = res.scalar_one_or_none()
        if not model:
            return None
        model.quota_daily = quota_daily
        model.quota_monthly = quota_monthly
        await self.db.commit()
        await self.db.refresh(model)
        return self._to_dict(model)
