from datetime import datetime, timezone
import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from apps.bilgeapi.repositories.interface import (
    IncidentRepository, DiagnosticRepository, FindingRepository,
    RecommendationRepository, RepairRequestRepository, AuditRepository, WebhookDeliveryRepository,
    ReleaseCheckRepository, ApiKeyRepository, ResearchRepository, ImprovementRepository,
    PrDraftRepository, PrVerificationRepository, PrReviewFeedbackRepository, PatchRevisionRepository,
    ReviewLedgerRepository,
    AIPatchSuggestionRepository, SystemFindingRepository,
    RemediationRunbookRepository, RemediationAttemptRepository,
    AutonomyDecisionRepository
)
from apps.bilgeapi.schemas.incident import IncidentCreate, IncidentResponse
from apps.bilgeapi.schemas.diagnostic import DiagnosticResult, DiagnosticStatus
from apps.bilgeapi.schemas.repair import RepairRequestCreate, RepairRequestResponse, ApprovalStatus, DispatchStatus
from apps.bilgeapi.schemas.audit import AuditEvent
from apps.bilgeapi.models.database import (
    IncidentModel, DiagnosticRunModel, FindingModel, RecommendationModel,
    RepairRequestModel, AuditEventModel, WebhookDeliveryModel, ReleaseCheckModel,
    ApiKeyModel, ResearchRequestModel, ResearchEvidenceModel, ImprovementProposalModel,
    PrDraftModel, PrVerificationModel, PrReviewFeedbackModel, PatchRevisionModel,
    ReviewLedgerEntryModel, AIPatchSuggestionModel, SystemFindingModel,
    RemediationRunbookModel, RemediationAttemptModel, AutonomyDecisionModel
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


class PostgresResearchRepository(ResearchRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    def _request_to_dict(self, model: ResearchRequestModel) -> Dict[str, Any]:
        return {
            "id": model.id,
            "incident_id": model.incident_id,
            "query": model.query,
            "status": model.status,
            "error_message": model.error_message,
            "tenant_id": model.tenant_id,
            "created_at": model.created_at,
            "updated_at": model.updated_at,
        }

    def _evidence_to_dict(self, model: ResearchEvidenceModel) -> Dict[str, Any]:
        return {
            "id": model.id,
            "research_id": model.research_id,
            "source_url": model.source_url,
            "source_domain": model.source_domain,
            "title": model.title,
            "snippet": model.snippet,
            "raw_content_summary": model.raw_content_summary,
            "content_hash": model.content_hash,
            "trust_score": model.trust_score,
            "retrieved_at": model.retrieved_at,
        }

    async def create_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        req_id = f"res_{uuid.uuid4().hex[:8]}"
        model = ResearchRequestModel(
            id=req_id,
            incident_id=request_data["incident_id"],
            query=request_data["query"],
            status=request_data.get("status", "PENDING"),
            error_message=request_data.get("error_message"),
            tenant_id=request_data.get("tenant_id"),
        )
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        return self._request_to_dict(model)

    async def get_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        res = await self.db.execute(select(ResearchRequestModel).where(ResearchRequestModel.id == request_id))
        model = res.scalar_one_or_none()
        return self._request_to_dict(model) if model else None

    async def update_request_status(self, request_id: str, status: str, error_message: Optional[str] = None) -> Optional[Dict[str, Any]]:
        res = await self.db.execute(select(ResearchRequestModel).where(ResearchRequestModel.id == request_id))
        model = res.scalar_one_or_none()
        if not model:
            return None
        model.status = status
        if error_message is not None:
            model.error_message = error_message
        await self.db.commit()
        await self.db.refresh(model)
        return self._request_to_dict(model)

    async def create_evidence(self, evidence_data: Dict[str, Any]) -> Dict[str, Any]:
        ev_id = f"evd_{uuid.uuid4().hex[:8]}"
        model = ResearchEvidenceModel(
            id=ev_id,
            research_id=evidence_data["research_id"],
            source_url=evidence_data["source_url"],
            source_domain=evidence_data["source_domain"],
            title=evidence_data.get("title"),
            snippet=evidence_data.get("snippet"),
            raw_content_summary=evidence_data.get("raw_content_summary"),
            content_hash=evidence_data["content_hash"],
            trust_score=evidence_data["trust_score"],
        )
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        return self._evidence_to_dict(model)

    async def list_evidences(self, research_id: str) -> List[Dict[str, Any]]:
        res = await self.db.execute(
            select(ResearchEvidenceModel)
            .where(ResearchEvidenceModel.research_id == research_id)
            .order_by(desc(ResearchEvidenceModel.trust_score))
        )
        models = res.scalars().all()
        return [self._evidence_to_dict(m) for m in models]

    async def get_tenant_daily_research_count(self, tenant_id: str, day: datetime) -> int:
        start_of_day = datetime(day.year, day.month, day.day, 0, 0, 0, tzinfo=timezone.utc)
        end_of_day = datetime(day.year, day.month, day.day, 23, 59, 59, tzinfo=timezone.utc)
        res = await self.db.execute(
            select(ResearchRequestModel)
            .where(ResearchRequestModel.tenant_id == tenant_id)
            .where(ResearchRequestModel.created_at >= start_of_day)
            .where(ResearchRequestModel.created_at <= end_of_day)
        )
        return len(res.scalars().all())


class PostgresImprovementRepository(ImprovementRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    def _proposal_to_dict(self, model: ImprovementProposalModel) -> Dict[str, Any]:
        return {
            "id": model.id,
            "research_id": model.research_id,
            "title": model.title,
            "rationale": model.rationale,
            "patch_code": model.patch_code,
            "risk_analysis": model.risk_analysis,
            "gate_status": model.gate_status,
            "gate_score": model.gate_score,
            "approval_status": model.approval_status,
            "approved_by": model.approved_by,
            "approved_at": model.approved_at,
            "ready_for_human_apply": model.ready_for_human_apply,
            "created_at": model.created_at,
            "updated_at": model.updated_at,
        }

    async def create_proposal(self, proposal_data: Dict[str, Any]) -> Dict[str, Any]:
        prop_id = f"prp_{uuid.uuid4().hex[:8]}"
        model = ImprovementProposalModel(
            id=prop_id,
            research_id=proposal_data["research_id"],
            title=proposal_data["title"],
            rationale=proposal_data["rationale"],
            patch_code=proposal_data["patch_code"],
            risk_analysis=proposal_data.get("risk_analysis"),
            gate_status=proposal_data.get("gate_status", "DRAFT"),
            gate_score=proposal_data.get("gate_score"),
            approval_status=proposal_data.get("approval_status", "REVIEW_REQUIRED"),
            ready_for_human_apply=proposal_data.get("ready_for_human_apply", False),
        )
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        return self._proposal_to_dict(model)

    async def get_proposal(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        res = await self.db.execute(select(ImprovementProposalModel).where(ImprovementProposalModel.id == proposal_id))
        model = res.scalar_one_or_none()
        return self._proposal_to_dict(model) if model else None

    async def update_proposal_gate(self, proposal_id: str, gate_status: str, gate_score: Optional[float] = None, risk_analysis: Optional[Dict[str, Any]] = None, approval_status: Optional[str] = None) -> Optional[Dict[str, Any]]:
        res = await self.db.execute(select(ImprovementProposalModel).where(ImprovementProposalModel.id == proposal_id))
        model = res.scalar_one_or_none()
        if not model:
            return None
        model.gate_status = gate_status
        if gate_score is not None:
            model.gate_score = gate_score
        if risk_analysis is not None:
            model.risk_analysis = risk_analysis
        if approval_status is not None:
            model.approval_status = approval_status
        await self.db.commit()
        await self.db.refresh(model)
        return self._proposal_to_dict(model)

    async def approve_proposal(self, proposal_id: str, approved_by: str, approved_at: datetime) -> Optional[Dict[str, Any]]:
        res = await self.db.execute(select(ImprovementProposalModel).where(ImprovementProposalModel.id == proposal_id))
        model = res.scalar_one_or_none()
        if not model:
            return None
        model.approval_status = "APPROVED"
        model.approved_by = approved_by
        model.approved_at = approved_at
        model.ready_for_human_apply = True
        await self.db.commit()
        await self.db.refresh(model)
        return self._proposal_to_dict(model)

    async def list_proposals(self) -> List[Dict[str, Any]]:
        res = await self.db.execute(select(ImprovementProposalModel).order_by(desc(ImprovementProposalModel.created_at)))
        models = res.scalars().all()
        return [self._proposal_to_dict(m) for m in models]


class PostgresPrDraftRepository(PrDraftRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    def _draft_to_dict(self, model: PrDraftModel) -> Dict[str, Any]:
        return {
            "id": model.id,
            "proposal_id": model.proposal_id,
            "provider": model.provider,
            "status": model.status,
            "github_pr_url": model.github_pr_url,
            "branch_name": model.branch_name,
            "title": model.title,
            "body": model.body,
            "evidence_hash": model.evidence_hash,
            "risk_level": model.risk_level,
            "risk_flags": model.risk_flags,
            "created_by": model.created_by,
            "created_at": model.created_at,
            "updated_at": model.updated_at,
        }

    async def create_pr_draft(self, draft_data: Dict[str, Any]) -> Dict[str, Any]:
        draft_id = f"prd_{uuid.uuid4().hex[:8]}"
        model = PrDraftModel(
            id=draft_id,
            proposal_id=draft_data["proposal_id"],
            provider=draft_data["provider"],
            status=draft_data.get("status", "PENDING"),
            github_pr_url=draft_data.get("github_pr_url"),
            branch_name=draft_data.get("branch_name"),
            title=draft_data["title"],
            body=draft_data["body"],
            evidence_hash=draft_data.get("evidence_hash"),
            risk_level=draft_data.get("risk_level", "LOW"),
            risk_flags=draft_data.get("risk_flags"),
            created_by=draft_data.get("created_by")
        )
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        return self._draft_to_dict(model)

    async def get_pr_draft(self, draft_id: str) -> Optional[Dict[str, Any]]:
        res = await self.db.execute(select(PrDraftModel).where(PrDraftModel.id == draft_id))
        model = res.scalar_one_or_none()
        return self._draft_to_dict(model) if model else None

    async def list_pr_drafts_by_proposal(self, proposal_id: str) -> List[Dict[str, Any]]:
        res = await self.db.execute(
            select(PrDraftModel)
            .where(PrDraftModel.proposal_id == proposal_id)
            .order_by(desc(PrDraftModel.created_at))
        )
        models = res.scalars().all()
        return [self._draft_to_dict(m) for m in models]

    async def update_pr_draft_status(self, draft_id: str, status: str, github_pr_url: Optional[str] = None, error_message: Optional[str] = None) -> Optional[Dict[str, Any]]:
        res = await self.db.execute(select(PrDraftModel).where(PrDraftModel.id == draft_id))
        model = res.scalar_one_or_none()
        if not model:
            return None
        model.status = status
        if github_pr_url is not None:
            model.github_pr_url = github_pr_url
        await self.db.commit()
        await self.db.refresh(model)
        return self._draft_to_dict(model)


class PostgresPrVerificationRepository(PrVerificationRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    def _verification_to_dict(self, model: PrVerificationModel) -> Dict[str, Any]:
        return {
            "id": model.id,
            "pr_draft_id": model.pr_draft_id,
            "proposal_id": model.proposal_id,
            "revision_id": model.revision_id,
            "ai_suggestion_id": model.ai_suggestion_id,
            "status": model.status,
            "review_score": model.review_score,
            "review_decision": model.review_decision,
            "risk_level": model.risk_level,
            "risk_flags": model.risk_flags,
            "affected_files": model.affected_files,
            "mutation_detected": model.mutation_detected,
            "test_files_present": model.test_files_present,
            "patch_size_lines": model.patch_size_lines,
            "test_plan": model.test_plan,
            "rollback_plan": model.rollback_plan,
            "verification_report": model.verification_report,
            "created_at": model.created_at,
            "updated_at": model.updated_at,
        }

    async def create_verification(self, verification_data: Dict[str, Any]) -> Dict[str, Any]:
        ver_id = f"prv_{uuid.uuid4().hex[:8]}"
        model = PrVerificationModel(
            id=ver_id,
            pr_draft_id=verification_data["pr_draft_id"],
            proposal_id=verification_data["proposal_id"],
            revision_id=verification_data.get("revision_id"),
            ai_suggestion_id=verification_data.get("ai_suggestion_id"),
            status=verification_data.get("status", "PENDING"),
            review_score=verification_data["review_score"],
            review_decision=verification_data["review_decision"],
            risk_level=verification_data["risk_level"],
            risk_flags=verification_data.get("risk_flags"),
            affected_files=verification_data.get("affected_files"),
            mutation_detected=verification_data.get("mutation_detected", False),
            test_files_present=verification_data.get("test_files_present", False),
            patch_size_lines=verification_data.get("patch_size_lines", 0),
            test_plan=verification_data.get("test_plan"),
            rollback_plan=verification_data.get("rollback_plan"),
            verification_report=verification_data.get("verification_report")
        )
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        return self._verification_to_dict(model)

    async def get_verification_by_pr_draft(self, pr_draft_id: str) -> Optional[Dict[str, Any]]:
        res = await self.db.execute(
            select(PrVerificationModel)
            .where(PrVerificationModel.pr_draft_id == pr_draft_id)
            .order_by(desc(PrVerificationModel.created_at))
            .limit(1)
        )
        model = res.scalar_one_or_none()
        return self._verification_to_dict(model) if model else None

    async def list_verifications_by_proposal(self, proposal_id: str) -> List[Dict[str, Any]]:
        res = await self.db.execute(
            select(PrVerificationModel)
            .where(PrVerificationModel.proposal_id == proposal_id)
            .order_by(desc(PrVerificationModel.created_at))
        )
        models = res.scalars().all()
        return [self._verification_to_dict(m) for m in models]

    async def get_verification_by_revision(self, revision_id: str) -> Optional[Dict[str, Any]]:
        res = await self.db.execute(
            select(PrVerificationModel)
            .where(PrVerificationModel.revision_id == revision_id)
            .order_by(desc(PrVerificationModel.created_at))
            .limit(1)
        )
        model = res.scalar_one_or_none()
        return self._verification_to_dict(model) if model else None

    async def get_verification_by_ai_suggestion(self, suggestion_id: str) -> Optional[Dict[str, Any]]:
        res = await self.db.execute(
            select(PrVerificationModel)
            .where(PrVerificationModel.ai_suggestion_id == suggestion_id)
            .order_by(desc(PrVerificationModel.created_at))
            .limit(1)
        )
        model = res.scalar_one_or_none()
        return self._verification_to_dict(model) if model else None


class PostgresPrReviewFeedbackRepository(PrReviewFeedbackRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    def _feedback_to_dict(self, model: PrReviewFeedbackModel) -> Dict[str, Any]:
        return {
            "id": model.id,
            "pr_draft_id": model.pr_draft_id,
            "reviewer_id": model.reviewer_id,
            "comment": model.comment,
            "status": model.status,
            "created_at": model.created_at,
            "updated_at": model.updated_at,
        }

    async def create_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        fb_id = f"pfb_{uuid.uuid4().hex[:8]}"
        model = PrReviewFeedbackModel(
            id=fb_id,
            pr_draft_id=feedback_data["pr_draft_id"],
            reviewer_id=feedback_data["reviewer_id"],
            comment=feedback_data["comment"],
            status=feedback_data.get("status", "PENDING")
        )
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        return self._feedback_to_dict(model)

    async def get_feedback(self, feedback_id: str) -> Optional[Dict[str, Any]]:
        res = await self.db.execute(
            select(PrReviewFeedbackModel).where(PrReviewFeedbackModel.id == feedback_id)
        )
        model = res.scalar_one_or_none()
        return self._feedback_to_dict(model) if model else None

    async def list_feedback_by_pr_draft(self, pr_draft_id: str) -> List[Dict[str, Any]]:
        res = await self.db.execute(
            select(PrReviewFeedbackModel)
            .where(PrReviewFeedbackModel.pr_draft_id == pr_draft_id)
            .order_by(desc(PrReviewFeedbackModel.created_at))
        )
        models = res.scalars().all()
        return [self._feedback_to_dict(m) for m in models]

    async def update_feedback_status(self, feedback_id: str, status: str) -> Optional[Dict[str, Any]]:
        res = await self.db.execute(
            select(PrReviewFeedbackModel).where(PrReviewFeedbackModel.id == feedback_id)
        )
        model = res.scalar_one_or_none()
        if not model:
            return None
        model.status = status
        await self.db.commit()
        await self.db.refresh(model)
        return self._feedback_to_dict(model)


class PostgresPatchRevisionRepository(PatchRevisionRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    def _revision_to_dict(self, model: PatchRevisionModel) -> Dict[str, Any]:
        return {
            "id": model.id,
            "pr_draft_id": model.pr_draft_id,
            "feedback_id": model.feedback_id,
            "revision_number": model.revision_number,
            "revised_patch_code": model.revised_patch_code,
            "risk_analysis": model.risk_analysis,
            "risk_level": model.risk_level,
            "verification_status": model.verification_status,
            "created_by": model.created_by,
            "created_at": model.created_at,
            "updated_at": model.updated_at,
        }

    async def create_revision(self, revision_data: Dict[str, Any]) -> Dict[str, Any]:
        rev_id = f"prev_{uuid.uuid4().hex[:8]}"
        model = PatchRevisionModel(
            id=rev_id,
            pr_draft_id=revision_data["pr_draft_id"],
            feedback_id=revision_data.get("feedback_id"),
            revision_number=revision_data["revision_number"],
            revised_patch_code=revision_data["revised_patch_code"],
            risk_analysis=revision_data.get("risk_analysis"),
            risk_level=revision_data.get("risk_level", "LOW"),
            verification_status=revision_data.get("verification_status", "PENDING"),
            created_by=revision_data.get("created_by")
        )
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        return self._revision_to_dict(model)

    async def get_revision(self, revision_id: str) -> Optional[Dict[str, Any]]:
        res = await self.db.execute(
            select(PatchRevisionModel).where(PatchRevisionModel.id == revision_id)
        )
        model = res.scalar_one_or_none()
        return self._revision_to_dict(model) if model else None

    async def get_latest_revision_number(self, pr_draft_id: str) -> int:
        res = await self.db.execute(
            select(func.coalesce(func.max(PatchRevisionModel.revision_number), 0))
            .where(PatchRevisionModel.pr_draft_id == pr_draft_id)
        )
        return res.scalar_one()

    async def list_revisions_by_pr_draft(self, pr_draft_id: str) -> List[Dict[str, Any]]:
        res = await self.db.execute(
            select(PatchRevisionModel)
            .where(PatchRevisionModel.pr_draft_id == pr_draft_id)
            .order_by(desc(PatchRevisionModel.revision_number))
        )
        models = res.scalars().all()
        return [self._revision_to_dict(m) for m in models]

    async def update_verification_status(self, revision_id: str, status: str) -> Optional[Dict[str, Any]]:
        res = await self.db.execute(
            select(PatchRevisionModel).where(PatchRevisionModel.id == revision_id)
        )
        model = res.scalar_one_or_none()
        if not model:
            return None
        model.verification_status = status
        await self.db.commit()
        await self.db.refresh(model)
        return self._revision_to_dict(model)


class PostgresReviewLedgerRepository(ReviewLedgerRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    def _entry_to_dict(self, model: ReviewLedgerEntryModel) -> Dict[str, Any]:
        return {
            "id": model.id,
            "chain_id": model.chain_id,
            "sequence_no": model.sequence_no,
            "event_type": model.event_type,
            "entity_type": model.entity_type,
            "entity_id": model.entity_id,
            "actor_id": model.actor_id,
            "previous_hash": model.previous_hash,
            "payload_hash": model.payload_hash,
            "event_hash": model.event_hash,
            "payload_summary": model.payload_summary,
            "created_at": model.created_at,
        }

    async def append_entry(self, entry_data: Dict[str, Any]) -> Dict[str, Any]:
        model = ReviewLedgerEntryModel(
            id=entry_data.get("id", f"rle_{uuid.uuid4().hex[:8]}"),
            chain_id=entry_data["chain_id"],
            sequence_no=entry_data["sequence_no"],
            event_type=entry_data["event_type"],
            entity_type=entry_data["entity_type"],
            entity_id=entry_data["entity_id"],
            actor_id=entry_data.get("actor_id"),
            previous_hash=entry_data.get("previous_hash"),
            payload_hash=entry_data["payload_hash"],
            event_hash=entry_data["event_hash"],
            payload_summary=entry_data.get("payload_summary"),
            created_at=entry_data.get("created_at") or datetime.now(timezone.utc),
        )
        self.db.add(model)
        try:
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise
        await self.db.refresh(model)
        return self._entry_to_dict(model)

    async def get_entry(self, entry_id: str) -> Optional[Dict[str, Any]]:
        res = await self.db.execute(select(ReviewLedgerEntryModel).where(ReviewLedgerEntryModel.id == entry_id))
        model = res.scalar_one_or_none()
        return self._entry_to_dict(model) if model else None

    async def get_latest_entry(self, chain_id: str) -> Optional[Dict[str, Any]]:
        res = await self.db.execute(
            select(ReviewLedgerEntryModel)
            .where(ReviewLedgerEntryModel.chain_id == chain_id)
            .order_by(desc(ReviewLedgerEntryModel.sequence_no))
            .limit(1)
        )
        model = res.scalar_one_or_none()
        return self._entry_to_dict(model) if model else None

    async def list_by_chain(self, chain_id: str) -> List[Dict[str, Any]]:
        res = await self.db.execute(
            select(ReviewLedgerEntryModel)
            .where(ReviewLedgerEntryModel.chain_id == chain_id)
            .order_by(ReviewLedgerEntryModel.sequence_no)
        )
        models = res.scalars().all()
        return [self._entry_to_dict(model) for model in models]

    async def list_recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        res = await self.db.execute(
            select(ReviewLedgerEntryModel)
            .order_by(desc(ReviewLedgerEntryModel.created_at))
            .limit(limit)
        )
        models = res.scalars().all()
        return [self._entry_to_dict(model) for model in models]


class PostgresAIPatchSuggestionRepository(AIPatchSuggestionRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    def _suggestion_to_dict(self, model: AIPatchSuggestionModel) -> Dict[str, Any]:
        return {
            "id": model.id,
            "pr_draft_id": model.pr_draft_id,
            "feedback_id": model.feedback_id,
            "revision_id": model.revision_id,
            "provider": model.provider,
            "model_name": model.model_name,
            "prompt_hash": model.prompt_hash,
            "context_summary": model.context_summary,
            "suggested_patch_code": model.suggested_patch_code,
            "rationale": model.rationale,
            "risk_notes": model.risk_notes,
            "risk_level": model.risk_level,
            "verification_id": model.verification_id,
            "status": model.status,
            "created_by": model.created_by,
            "created_at": model.created_at,
            "updated_at": model.updated_at,
        }

    async def create_suggestion(self, data: Dict[str, Any]) -> Dict[str, Any]:
        model = AIPatchSuggestionModel(
            id=data.get("id", f"ais_{uuid.uuid4().hex[:8]}"),
            pr_draft_id=data["pr_draft_id"],
            feedback_id=data.get("feedback_id"),
            revision_id=data.get("revision_id"),
            provider=data.get("provider", "mock"),
            model_name=data.get("model_name"),
            prompt_hash=data["prompt_hash"],
            context_summary=data.get("context_summary"),
            suggested_patch_code=data["suggested_patch_code"],
            rationale=data.get("rationale"),
            risk_notes=data.get("risk_notes"),
            risk_level=data.get("risk_level", "LOW"),
            verification_id=data.get("verification_id"),
            status=data.get("status", "GENERATED"),
            created_by=data.get("created_by"),
        )
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        return self._suggestion_to_dict(model)


class PostgresSystemFindingRepository(SystemFindingRepository):
    TERMINAL_STATUSES = {"DISMISSED", "RESOLVED"}

    def __init__(self, db: AsyncSession):
        self.db = db

    def _finding_to_dict(self, model: SystemFindingModel) -> Dict[str, Any]:
        return {
            "id": model.id,
            "tenant_id": model.tenant_id,
            "source_type": model.source_type,
            "source_id": model.source_id,
            "source_hash": model.source_hash,
            "title": model.title,
            "description": model.description,
            "severity": model.severity,
            "risk_score": model.risk_score,
            "status": model.status,
            "evidence_summary": model.evidence_summary,
            "recommended_action": model.recommended_action,
            "human_gate_payload": model.human_gate_payload,
            "occurrence_count": model.occurrence_count,
            "first_seen_at": model.first_seen_at,
            "last_seen_at": model.last_seen_at,
            "acknowledged_by": model.acknowledged_by,
            "acknowledged_at": model.acknowledged_at,
            "dismissed_by": model.dismissed_by,
            "dismissed_at": model.dismissed_at,
            "resolved_by": model.resolved_by,
            "resolved_at": model.resolved_at,
            "bilgeapi_research_id": model.bilgeapi_research_id,
            "bilgeapi_proposal_id": model.bilgeapi_proposal_id,
            "bilgeapi_pr_draft_id": model.bilgeapi_pr_draft_id,
            "bilgeapi_verification_id": model.bilgeapi_verification_id,
            "bilgeapi_ledger_chain_id": model.bilgeapi_ledger_chain_id,
            "created_by": model.created_by,
            "correlation_id": model.correlation_id,
            "created_at": model.created_at,
            "updated_at": model.updated_at,
        }

    async def create_finding(self, finding_data: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        model = SystemFindingModel(
            id=finding_data.get("id", f"sf_{uuid.uuid4().hex[:8]}"),
            tenant_id=finding_data.get("tenant_id"),
            source_type=finding_data["source_type"],
            source_id=finding_data["source_id"],
            source_hash=finding_data["source_hash"],
            title=finding_data["title"],
            description=finding_data["description"],
            severity=finding_data["severity"],
            risk_score=finding_data["risk_score"],
            status=finding_data.get("status", "OPEN"),
            evidence_summary=finding_data.get("evidence_summary"),
            recommended_action=finding_data.get("recommended_action"),
            human_gate_payload=finding_data.get("human_gate_payload"),
            occurrence_count=finding_data.get("occurrence_count", 1),
            first_seen_at=finding_data.get("first_seen_at") or now,
            last_seen_at=finding_data.get("last_seen_at") or now,
            bilgeapi_research_id=finding_data.get("bilgeapi_research_id"),
            bilgeapi_proposal_id=finding_data.get("bilgeapi_proposal_id"),
            bilgeapi_pr_draft_id=finding_data.get("bilgeapi_pr_draft_id"),
            bilgeapi_verification_id=finding_data.get("bilgeapi_verification_id"),
            bilgeapi_ledger_chain_id=finding_data.get("bilgeapi_ledger_chain_id"),
            created_by=finding_data.get("created_by"),
            correlation_id=finding_data.get("correlation_id"),
        )
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        return self._finding_to_dict(model)

    async def get_finding(self, finding_id: str) -> Optional[Dict[str, Any]]:
        res = await self.db.execute(select(SystemFindingModel).where(SystemFindingModel.id == finding_id))
        model = res.scalar_one_or_none()
        return self._finding_to_dict(model) if model else None

    async def get_open_by_source_hash(self, source_hash: str) -> Optional[Dict[str, Any]]:
        res = await self.db.execute(
            select(SystemFindingModel)
            .where(SystemFindingModel.source_hash == source_hash)
            .where(SystemFindingModel.status.notin_(self.TERMINAL_STATUSES))
            .order_by(desc(SystemFindingModel.created_at))
            .limit(1)
        )
        model = res.scalar_one_or_none()
        return self._finding_to_dict(model) if model else None

    async def get_by_source_hash(self, source_hash: str) -> Optional[Dict[str, Any]]:
        res = await self.db.execute(
            select(SystemFindingModel)
            .where(SystemFindingModel.source_hash == source_hash)
            .order_by(desc(SystemFindingModel.created_at))
            .limit(1)
        )
        model = res.scalar_one_or_none()
        return self._finding_to_dict(model) if model else None

    async def list_findings(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        stmt = select(SystemFindingModel)
        if status:
            stmt = stmt.where(SystemFindingModel.status == status)
        if severity:
            stmt = stmt.where(SystemFindingModel.severity == severity)
        stmt = stmt.order_by(desc(SystemFindingModel.created_at)).limit(limit)
        res = await self.db.execute(stmt)
        return [self._finding_to_dict(model) for model in res.scalars().all()]

    async def increment_occurrence(
        self,
        finding_id: str,
        evidence_summary: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        res = await self.db.execute(select(SystemFindingModel).where(SystemFindingModel.id == finding_id))
        model = res.scalar_one_or_none()
        if not model or model.status in self.TERMINAL_STATUSES:
            return None
        model.occurrence_count += 1
        model.last_seen_at = datetime.now(timezone.utc)
        if evidence_summary is not None:
            model.evidence_summary = evidence_summary
        await self.db.commit()
        await self.db.refresh(model)
        return self._finding_to_dict(model)

    async def update_status(
        self,
        finding_id: str,
        status: str,
        actor_id: str,
    ) -> Optional[Dict[str, Any]]:
        res = await self.db.execute(select(SystemFindingModel).where(SystemFindingModel.id == finding_id))
        model = res.scalar_one_or_none()
        if not model:
            return None
        now = datetime.now(timezone.utc)
        model.status = status
        if status == "ACKNOWLEDGED":
            model.acknowledged_by = actor_id
            model.acknowledged_at = now
        elif status == "DISMISSED":
            model.dismissed_by = actor_id
            model.dismissed_at = now
        elif status == "RESOLVED":
            model.resolved_by = actor_id
            model.resolved_at = now
        await self.db.commit()
        await self.db.refresh(model)
        return self._finding_to_dict(model)

    async def get_suggestion(self, suggestion_id: str) -> Optional[Dict[str, Any]]:
        res = await self.db.execute(select(AIPatchSuggestionModel).where(AIPatchSuggestionModel.id == suggestion_id))
        model = res.scalar_one_or_none()
        return self._suggestion_to_dict(model) if model else None

    async def list_suggestions_by_pr_draft(self, pr_draft_id: str) -> List[Dict[str, Any]]:
        res = await self.db.execute(
            select(AIPatchSuggestionModel)
            .where(AIPatchSuggestionModel.pr_draft_id == pr_draft_id)
            .order_by(desc(AIPatchSuggestionModel.created_at))
        )
        return [self._suggestion_to_dict(model) for model in res.scalars().all()]

    async def update_suggestion_status(self, suggestion_id: str, status: str) -> Optional[Dict[str, Any]]:
        res = await self.db.execute(select(AIPatchSuggestionModel).where(AIPatchSuggestionModel.id == suggestion_id))
        model = res.scalar_one_or_none()
        if not model:
            return None
        model.status = status
        await self.db.commit()
        await self.db.refresh(model)
        return self._suggestion_to_dict(model)

    async def attach_verification(
        self,
        suggestion_id: str,
        verification_id: str,
        risk_level: str,
        status: str,
    ) -> Optional[Dict[str, Any]]:
        res = await self.db.execute(select(AIPatchSuggestionModel).where(AIPatchSuggestionModel.id == suggestion_id))
        model = res.scalar_one_or_none()
        if not model:
            return None
        model.verification_id = verification_id
        model.risk_level = risk_level
        model.status = status
        await self.db.commit()
        await self.db.refresh(model)
        return self._suggestion_to_dict(model)


class PostgresRemediationRunbookRepository(RemediationRunbookRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    def _to_dict(self, model: RemediationRunbookModel) -> Dict[str, Any]:
        return {
            "id": model.id,
            "name": model.name,
            "action_type": model.action_type,
            "severity_allowed": model.severity_allowed,
            "requires_human_gate": model.requires_human_gate,
            "enabled": model.enabled,
            "execution_mode": model.execution_mode,
            "max_attempts": model.max_attempts,
            "cooldown_seconds": model.cooldown_seconds,
            "safety_notes": model.safety_notes,
            "created_at": model.created_at,
            "updated_at": model.updated_at,
        }

    async def create_runbook(self, runbook_data: Dict[str, Any]) -> Dict[str, Any]:
        rb_id = f"rbk_{uuid.uuid4().hex[:8]}"
        model = RemediationRunbookModel(
            id=rb_id,
            name=runbook_data["name"],
            action_type=runbook_data["action_type"],
            severity_allowed=runbook_data["severity_allowed"],
            requires_human_gate=runbook_data.get("requires_human_gate", True),
            enabled=runbook_data.get("enabled", False),
            execution_mode=runbook_data.get("execution_mode", "MANUAL"),
            max_attempts=runbook_data.get("max_attempts", 2),
            cooldown_seconds=runbook_data.get("cooldown_seconds", 300),
            safety_notes=runbook_data.get("safety_notes"),
        )
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        return self._to_dict(model)

    async def get_runbook(self, runbook_id: str) -> Optional[Dict[str, Any]]:
        res = await self.db.execute(select(RemediationRunbookModel).where(RemediationRunbookModel.id == runbook_id))
        model = res.scalar_one_or_none()
        return self._to_dict(model) if model else None

    async def get_runbook_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        res = await self.db.execute(select(RemediationRunbookModel).where(RemediationRunbookModel.name == name))
        model = res.scalar_one_or_none()
        return self._to_dict(model) if model else None

    async def list_runbooks(self) -> List[Dict[str, Any]]:
        res = await self.db.execute(select(RemediationRunbookModel).order_by(RemediationRunbookModel.name))
        return [self._to_dict(m) for m in res.scalars().all()]

    async def update_runbook_enabled(self, runbook_id: str, enabled: bool) -> Optional[Dict[str, Any]]:
        res = await self.db.execute(select(RemediationRunbookModel).where(RemediationRunbookModel.id == runbook_id))
        model = res.scalar_one_or_none()
        if not model:
            return None
        model.enabled = enabled
        await self.db.commit()
        await self.db.refresh(model)
        return self._to_dict(model)


class PostgresRemediationAttemptRepository(RemediationAttemptRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    def _to_dict(self, model: RemediationAttemptModel) -> Dict[str, Any]:
        return {
            "id": model.id,
            "finding_id": model.finding_id,
            "runbook_id": model.runbook_id,
            "action_type": model.action_type,
            "status": model.status,
            "attempt_no": model.attempt_no,
            "before_health": model.before_health,
            "after_health": model.after_health,
            "output_summary": model.output_summary,
            "error_message": model.error_message,
            "policy_decision": model.policy_decision,
            "forbidden_actions_checked": model.forbidden_actions_checked,
            "ledger_chain_id": model.ledger_chain_id,
            "created_by": model.created_by,
            "started_at": model.started_at,
            "completed_at": model.completed_at,
            "created_at": model.created_at,
            "updated_at": model.updated_at,
        }

    async def create_attempt(self, attempt_data: Dict[str, Any]) -> Dict[str, Any]:
        att_id = f"att_{uuid.uuid4().hex[:8]}"
        model = RemediationAttemptModel(
            id=att_id,
            finding_id=attempt_data["finding_id"],
            runbook_id=attempt_data.get("runbook_id"),
            action_type=attempt_data["action_type"],
            status=attempt_data.get("status", "PENDING"),
            attempt_no=attempt_data.get("attempt_no", 1),
            before_health=attempt_data.get("before_health"),
            after_health=attempt_data.get("after_health"),
            output_summary=attempt_data.get("output_summary"),
            error_message=attempt_data.get("error_message"),
            policy_decision=attempt_data.get("policy_decision"),
            forbidden_actions_checked=attempt_data.get("forbidden_actions_checked"),
            ledger_chain_id=attempt_data.get("ledger_chain_id"),
            created_by=attempt_data.get("created_by"),
            started_at=attempt_data.get("started_at"),
            completed_at=attempt_data.get("completed_at"),
        )
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        return self._to_dict(model)

    async def get_attempt(self, attempt_id: str) -> Optional[Dict[str, Any]]:
        res = await self.db.execute(select(RemediationAttemptModel).where(RemediationAttemptModel.id == attempt_id))
        model = res.scalar_one_or_none()
        return self._to_dict(model) if model else None

    async def list_attempts_by_finding(self, finding_id: str) -> List[Dict[str, Any]]:
        res = await self.db.execute(
            select(RemediationAttemptModel)
            .where(RemediationAttemptModel.finding_id == finding_id)
            .order_by(desc(RemediationAttemptModel.created_at))
        )
        return [self._to_dict(m) for m in res.scalars().all()]

    async def get_latest_attempt_for_finding(self, finding_id: str) -> Optional[Dict[str, Any]]:
        res = await self.db.execute(
            select(RemediationAttemptModel)
            .where(RemediationAttemptModel.finding_id == finding_id)
            .order_by(desc(RemediationAttemptModel.created_at))
            .limit(1)
        )
        model = res.scalar_one_or_none()
        return self._to_dict(model) if model else None

    async def list_attempts(self, limit: int = 50) -> List[Dict[str, Any]]:
        res = await self.db.execute(
            select(RemediationAttemptModel)
            .order_by(desc(RemediationAttemptModel.created_at))
            .limit(limit)
        )
        return [self._to_dict(m) for m in res.scalars().all()]

    async def update_attempt(self, attempt_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        res = await self.db.execute(select(RemediationAttemptModel).where(RemediationAttemptModel.id == attempt_id))
        model = res.scalar_one_or_none()
        if not model:
            return None
        for k, v in updates.items():
            if hasattr(model, k):
                setattr(model, k, v)
        await self.db.commit()
        await self.db.refresh(model)
        return self._to_dict(model)


class PostgresAutonomyDecisionRepository(AutonomyDecisionRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    def _to_dict(self, model: AutonomyDecisionModel) -> Dict[str, Any]:
        return {
            "decision_id": model.id,
            "incident_id": model.incident_id,
            "correlation_id": model.correlation_id,
            "classification": model.classification,
            "risk_score": model.risk_score,
            "risk_level": model.risk_level,
            "active_autonomy_mode": model.active_autonomy_mode,
            "eligibility": model.eligibility,
            "action_type": model.action_type,
            "decision_reason": model.decision_reason,
            "requires_human_gate": model.requires_human_gate,
            "human_gate_type": model.human_gate_type,
            "created_at": model.created_at
        }

    async def create(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        dec_id = f"dec_{uuid.uuid4().hex[:8]}"
        model = AutonomyDecisionModel(
            id=dec_id,
            incident_id=decision["incident_id"],
            correlation_id=decision["correlation_id"],
            classification=decision["classification"],
            risk_score=decision["risk_score"],
            risk_level=decision["risk_level"],
            active_autonomy_mode=decision["active_autonomy_mode"],
            eligibility=decision["eligibility"],
            action_type=decision.get("action_type"),
            decision_reason=decision["decision_reason"],
            requires_human_gate=decision["requires_human_gate"],
            human_gate_type=decision.get("human_gate_type")
        )
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        return self._to_dict(model)

    async def get(self, decision_id: str) -> Optional[Dict[str, Any]]:
        res = await self.db.execute(select(AutonomyDecisionModel).where(AutonomyDecisionModel.id == decision_id))
        model = res.scalar_one_or_none()
        return self._to_dict(model) if model else None

    async def list_by_incident(self, incident_id: str) -> List[Dict[str, Any]]:
        res = await self.db.execute(
            select(AutonomyDecisionModel)
            .where(AutonomyDecisionModel.incident_id == incident_id)
            .order_by(desc(AutonomyDecisionModel.created_at))
        )
        return [self._to_dict(m) for m in res.scalars().all()]

