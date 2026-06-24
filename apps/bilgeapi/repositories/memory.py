
import inspect
import asyncio
from functools import wraps
from datetime import datetime

def tenant_compatibility_bridge(func):
    sig = inspect.signature(func)
    @wraps(func)
    async def wrapper(*args, **kwargs):
        params = list(sig.parameters.values())
        has_tenant = 'tenant_id' in sig.parameters
        new_args = list(args)
        
        tenant_idx = -1
        bypass_idx = -1
        day_idx = -1
        for idx, param in enumerate(params):
            if param.name == 'tenant_id':
                tenant_idx = idx
            elif param.name == 'bypass_tenant':
                bypass_idx = idx
            elif param.name == 'day':
                day_idx = idx
                
        if tenant_idx != -1 and len(new_args) > tenant_idx:
            val = new_args[tenant_idx]
            if isinstance(val, bool) and bypass_idx != -1:
                if len(new_args) > bypass_idx:
                    new_args[bypass_idx] = val
                else:
                    kwargs['bypass_tenant'] = val
                new_args[tenant_idx] = "default"
            elif isinstance(val, datetime) and day_idx != -1:
                if len(new_args) > day_idx:
                    new_args[day_idx] = val
                else:
                    kwargs['day'] = val
                new_args[tenant_idx] = "default"
            elif val is None:
                new_args[tenant_idx] = "default"
            elif val == "":
                raise ValueError("tenant_id is required")
                
        if 'tenant_id' in kwargs:
            val = kwargs['tenant_id']
            if isinstance(val, bool) and bypass_idx != -1:
                kwargs['bypass_tenant'] = val
                kwargs['tenant_id'] = "default"
            elif isinstance(val, datetime) and day_idx != -1:
                kwargs['day'] = val
                kwargs['tenant_id'] = "default"
            elif val is None:
                kwargs['tenant_id'] = "default"
            elif val == "":
                raise ValueError("tenant_id is required")
                
        if has_tenant:
            if len(new_args) <= tenant_idx and 'tenant_id' not in kwargs:
                kwargs['tenant_id'] = "default"
                
        try:
            bound = sig.bind(*new_args, **kwargs)
            bound.apply_defaults()
        except TypeError as err:
            raise err
            
        t_val = bound.arguments.get('tenant_id')
        if t_val == "":
            raise ValueError("tenant_id is required")
            
        return await func(*bound.args, **bound.kwargs)
    return wrapper

def compatibility_class_decorator(cls):
    for name, method in list(cls.__dict__.items()):
        if asyncio.iscoroutinefunction(method) or inspect.iscoroutinefunction(method):
            setattr(cls, name, tenant_compatibility_bridge(method))
    return cls

import uuid
import asyncio
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from apps.bilgeapi.repositories.interface import (
    IncidentRepository,
    DiagnosticRepository,
    FindingRepository,
    RecommendationRepository,
    RepairRequestRepository,
    AuditRepository,
    WebhookDeliveryRepository,
    ReleaseCheckRepository,
    ApiKeyRepository,
    ResearchRepository,
    ImprovementRepository,
    PrDraftRepository,
    PrVerificationRepository,
    PrReviewFeedbackRepository,
    PatchRevisionRepository,
    ReviewLedgerRepository,
    AIPatchSuggestionRepository,
    SystemFindingRepository,
    RemediationRunbookRepository,
    RemediationAttemptRepository,
    AutonomyDecisionRepository
)
from apps.bilgeapi.schemas.incident import IncidentCreate, IncidentResponse
from apps.bilgeapi.schemas.diagnostic import DiagnosticResult, DiagnosticStatus
from apps.bilgeapi.schemas.repair import RepairRequestCreate, RepairRequestResponse, ApprovalStatus, DispatchStatus
from apps.bilgeapi.schemas.audit import AuditEvent

class MemoryRepositoriesContainer:
    def __init__(self):
        self.incidents: Dict[str, IncidentResponse] = {}
        self.diagnostics: Dict[str, DiagnosticResult] = {}
        self.findings: Dict[str, List[Dict[str, Any]]] = {}
        self.recommendations: Dict[str, List[Dict[str, Any]]] = {}
        self.repair_requests: Dict[str, RepairRequestResponse] = {}
        self.audit_events: List[AuditEvent] = []
        self.webhook_deliveries: List[Dict[str, Any]] = []
        self.release_checks: List[Dict[str, Any]] = []
        self.api_keys: Dict[str, Dict[str, Any]] = {}
        self.research_requests: Dict[str, Dict[str, Any]] = {}
        self.research_evidences: Dict[str, Dict[str, Any]] = {}
        self.improvement_proposals: Dict[str, Dict[str, Any]] = {}
        self.pr_drafts: Dict[str, Dict[str, Any]] = {}
        self.pr_verifications: Dict[str, Dict[str, Any]] = {}
        self.pr_review_feedbacks: Dict[str, Dict[str, Any]] = {}
        self.patch_revisions: Dict[str, Dict[str, Any]] = {}
        self.review_ledger_entries: Dict[str, Dict[str, Any]] = {}
        self.ai_patch_suggestions: Dict[str, Dict[str, Any]] = {}
        self.system_findings: Dict[str, Dict[str, Any]] = {}
        self.remediation_runbooks: Dict[str, Dict[str, Any]] = {}
        self.remediation_attempts: Dict[str, Dict[str, Any]] = {}
        self.autonomy_decisions: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    def clear_all(self):
        self.incidents.clear()
        self.diagnostics.clear()
        self.findings.clear()
        self.recommendations.clear()
        self.repair_requests.clear()
        self.audit_events.clear()
        self.webhook_deliveries.clear()
        self.release_checks.clear()
        self.api_keys.clear()
        self.research_requests.clear()
        self.research_evidences.clear()
        self.improvement_proposals.clear()
        self.pr_drafts.clear()
        self.pr_verifications.clear()
        self.pr_review_feedbacks.clear()
        self.patch_revisions.clear()
        self.review_ledger_entries.clear()
        self.ai_patch_suggestions.clear()
        self.system_findings.clear()
        self.remediation_runbooks.clear()
        self.remediation_attempts.clear()
        self.autonomy_decisions.clear()

memory_repositories = MemoryRepositoriesContainer()

def _log_memory_security_event(tenant_id: str, action: str, target: str, actual_tenant: Optional[str]):
    event = AuditEvent(
        id=f"evt_{uuid.uuid4().hex[:8]}",
        event_type="CROSS_TENANT_ACCESS_DENIED",
        actor_id="anonymous",
        actor_type="system",
        entity_type="security_gate",
        entity_id=target,
        before_state={"requested_tenant": tenant_id},
        after_state={"actual_tenant": actual_tenant},
        metadata={"action": action},
        created_at=datetime.now(timezone.utc)
    )
    object.__setattr__(event, 'tenant_id', tenant_id)
    memory_repositories.audit_events.append(event)

def _check_tenant(obj: Any, tenant_id: str, bypass_tenant: bool, action: str, target: str) -> bool:
    if bypass_tenant:
        return True
    if not tenant_id:
        raise ValueError("tenant_id is required (missing tenant context fails closed)")
    
    obj_tenant = getattr(obj, "tenant_id", None) if not isinstance(obj, dict) else obj.get("tenant_id")
    if obj_tenant is None:
        obj_tenant = "default"
    if obj_tenant != tenant_id:
        _log_memory_security_event(tenant_id, action, target, obj_tenant)
        return False
    return True

@compatibility_class_decorator
class InMemoryIncidentRepository(IncidentRepository):
    async def create(self, incident: IncidentCreate, tenant_id: str = "default") -> IncidentResponse:
        if not tenant_id:
            tenant_id = "default"
        async with memory_repositories._lock:
            inc_id = f"inc_{uuid.uuid4().hex[:8]}"
            response = IncidentResponse(
                id=inc_id,
                created_at=datetime.now(timezone.utc),
                **incident.model_dump()
            )
            object.__setattr__(response, 'tenant_id', tenant_id)
            memory_repositories.incidents[inc_id] = response
            return response

    async def get(self, incident_id: str, tenant_id: str = "default", bypass_tenant: bool = False) -> Optional[IncidentResponse]:
        if not tenant_id:
            tenant_id = "default"
        async with memory_repositories._lock:
            obj = memory_repositories.incidents.get(incident_id)
            if not obj:
                return None
            if not _check_tenant(obj, tenant_id, bypass_tenant, "get", f"incident:{incident_id}"):
                return None
            return obj

    async def list_all(self, tenant_id: str = "default", project_key: Optional[str] = None, bypass_tenant: bool = False) -> List[IncidentResponse]:
        if not tenant_id:
            tenant_id = "default"
        if not bypass_tenant and not tenant_id:
            raise ValueError("tenant_id is required")
        async with memory_repositories._lock:
            res = []
            for obj in memory_repositories.incidents.values():
                if _check_tenant(obj, tenant_id, bypass_tenant, "list", f"incident:{obj.id}"):
                    if not project_key or obj.project_key == project_key:
                        res.append(obj)
            return sorted(res, key=lambda x: x.created_at, reverse=True)


@compatibility_class_decorator
class InMemoryDiagnosticRepository(DiagnosticRepository):
    async def create(self, incident_id: str, tenant_id: str = "default") -> DiagnosticResult:
        if not tenant_id:
            tenant_id = "default"
        async with memory_repositories._lock:
            diag_id = f"diag_{uuid.uuid4().hex[:8]}"
            result = DiagnosticResult(
                diagnostic_id=diag_id,
                incident_id=incident_id,
                status=DiagnosticStatus.QUEUED,
                created_at=datetime.now(timezone.utc)
            )
            object.__setattr__(result, 'tenant_id', tenant_id)
            memory_repositories.diagnostics[diag_id] = result
            return result

    async def get(self, diagnostic_id: str, tenant_id: str = "default", bypass_tenant: bool = False) -> Optional[DiagnosticResult]:
        if not tenant_id:
            tenant_id = "default"
        async with memory_repositories._lock:
            obj = memory_repositories.diagnostics.get(diagnostic_id)
            if not obj:
                return None
            if not _check_tenant(obj, tenant_id, bypass_tenant, "get", f"diagnostic:{diagnostic_id}"):
                return None
            return obj

    async def update(self, diagnostic_id: str, status: DiagnosticStatus, tenant_id: str = "default", bypass_tenant: bool = False, **kwargs) -> Optional[DiagnosticResult]:
        if not tenant_id:
            tenant_id = "default"
        async with memory_repositories._lock:
            obj = memory_repositories.diagnostics.get(diagnostic_id)
            if not obj:
                return None
            if not _check_tenant(obj, tenant_id, bypass_tenant, "update", f"diagnostic:{diagnostic_id}"):
                return None
            
            updated_data = obj.model_dump()
            updated_data["status"] = status
            for k, v in kwargs.items():
                updated_data[k] = v
            
            if status in (DiagnosticStatus.COMPLETED, DiagnosticStatus.FAILED) and not updated_data.get("completed_at"):
                updated_data["completed_at"] = datetime.now(timezone.utc)
                
            updated_diag = DiagnosticResult(**updated_data)
            object.__setattr__(updated_diag, 'tenant_id', getattr(obj, "tenant_id", None))
            memory_repositories.diagnostics[diagnostic_id] = updated_diag
            return updated_diag

    async def list_all(self, tenant_id: str = "default", bypass_tenant: bool = False) -> List[DiagnosticResult]:
        if not tenant_id:
            tenant_id = "default"
        if not bypass_tenant and not tenant_id:
            raise ValueError("tenant_id is required")
        async with memory_repositories._lock:
            res = []
            for obj in memory_repositories.diagnostics.values():
                if _check_tenant(obj, tenant_id, bypass_tenant, "list", f"diagnostic:{obj.diagnostic_id}"):
                    res.append(obj)
            return sorted(res, key=lambda x: x.created_at, reverse=True)


@compatibility_class_decorator
class InMemoryFindingRepository(FindingRepository):
    async def create(self, diagnostic_id: str, finding_data: Dict[str, Any], tenant_id: str = "default") -> Dict[str, Any]:
        if not tenant_id:
            tenant_id = "default"
        async with memory_repositories._lock:
            if diagnostic_id not in memory_repositories.findings:
                memory_repositories.findings[diagnostic_id] = []
            
            f_id = f"find_{uuid.uuid4().hex[:8]}"
            finding = {"id": f_id, "diagnostic_id": diagnostic_id, "tenant_id": tenant_id, **finding_data}
            memory_repositories.findings[diagnostic_id].append(finding)
            return finding

    async def list_by_diagnostic(self, diagnostic_id: str, tenant_id: str = "default", bypass_tenant: bool = False) -> List[Dict[str, Any]]:
        if not tenant_id:
            tenant_id = "default"
        async with memory_repositories._lock:
            raw_list = memory_repositories.findings.get(diagnostic_id, [])
            res = []
            for f in raw_list:
                if _check_tenant(f, tenant_id, bypass_tenant, "list_findings", f"finding:{f.get('id')}"):
                    res.append(f)
            return res


@compatibility_class_decorator
class InMemoryRecommendationRepository(RecommendationRepository):
    async def create(self, diagnostic_id: str, recommendation_data: Dict[str, Any], tenant_id: str = "default") -> Dict[str, Any]:
        if not tenant_id:
            tenant_id = "default"
        async with memory_repositories._lock:
            if diagnostic_id not in memory_repositories.recommendations:
                memory_repositories.recommendations[diagnostic_id] = []
            
            r_id = f"rec_{uuid.uuid4().hex[:8]}"
            recommendation = {"id": r_id, "diagnostic_id": diagnostic_id, "tenant_id": tenant_id, **recommendation_data}
            memory_repositories.recommendations[diagnostic_id].append(recommendation)
            return recommendation

    async def list_by_diagnostic(self, diagnostic_id: str, tenant_id: str = "default", bypass_tenant: bool = False) -> List[Dict[str, Any]]:
        if not tenant_id:
            tenant_id = "default"
        async with memory_repositories._lock:
            raw_list = memory_repositories.recommendations.get(diagnostic_id, [])
            res = []
            for r in raw_list:
                if _check_tenant(r, tenant_id, bypass_tenant, "list_recommendations", f"recommendation:{r.get('id')}"):
                    res.append(r)
            return res


@compatibility_class_decorator
class InMemoryRepairRequestRepository(RepairRequestRepository):
    async def create(self, diagnostic_id: str, request: RepairRequestCreate, tenant_id: str = "default") -> RepairRequestResponse:
        if not tenant_id:
            tenant_id = "default"
        async with memory_repositories._lock:
            rep_id = f"rep_{uuid.uuid4().hex[:8]}"
            now = datetime.now(timezone.utc)
            response = RepairRequestResponse(
                id=rep_id,
                diagnostic_id=diagnostic_id,
                requested_by=request.requested_by,
                approved_by=request.approved_by,
                approval_status=request.approval_status,
                risk_score=request.risk_score,
                risk_reason=request.risk_reason,
                dispatch_status=DispatchStatus.PENDING,
                external_reference=None,
                approval_required=request.approval_required,
                rejection_reason=None,
                approved_at=request.approved_at,
                rejected_at=None,
                created_at=now,
                updated_at=now
            )
            object.__setattr__(response, 'tenant_id', tenant_id)
            memory_repositories.repair_requests[rep_id] = response
            return response

    async def get(self, repair_request_id: str, tenant_id: str = "default", bypass_tenant: bool = False) -> Optional[RepairRequestResponse]:
        if not tenant_id:
            tenant_id = "default"
        async with memory_repositories._lock:
            obj = memory_repositories.repair_requests.get(repair_request_id)
            if not obj:
                return None
            if not _check_tenant(obj, tenant_id, bypass_tenant, "get", f"repair_request:{repair_request_id}"):
                return None
            return obj

    async def update(self, repair_request_id: str, approval_status: ApprovalStatus, dispatch_status: DispatchStatus, tenant_id: str = "default", bypass_tenant: bool = False, **kwargs) -> Optional[RepairRequestResponse]:
        if not tenant_id:
            tenant_id = "default"
        async with memory_repositories._lock:
            obj = memory_repositories.repair_requests.get(repair_request_id)
            if not obj:
                return None
            if not _check_tenant(obj, tenant_id, bypass_tenant, "update", f"repair_request:{repair_request_id}"):
                return None
            
            updated_data = obj.model_dump()
            updated_data["approval_status"] = approval_status
            updated_data["dispatch_status"] = dispatch_status
            updated_data["updated_at"] = datetime.now(timezone.utc)
            for k, v in kwargs.items():
                updated_data[k] = v
            
            updated_rep = RepairRequestResponse(**updated_data)
            object.__setattr__(updated_rep, 'tenant_id', getattr(obj, "tenant_id", None))
            memory_repositories.repair_requests[repair_request_id] = updated_rep
            return updated_rep

    async def list_all(self, tenant_id: str = "default", bypass_tenant: bool = False) -> List[RepairRequestResponse]:
        if not tenant_id:
            tenant_id = "default"
        if not bypass_tenant and not tenant_id:
            raise ValueError("tenant_id is required")
        async with memory_repositories._lock:
            res = []
            for obj in memory_repositories.repair_requests.values():
                if _check_tenant(obj, tenant_id, bypass_tenant, "list", f"repair_request:{obj.id}"):
                    res.append(obj)
            return sorted(res, key=lambda x: x.created_at, reverse=True)


@compatibility_class_decorator
class InMemoryAuditRepository(AuditRepository):
    async def write(self, event: AuditEvent, tenant_id: str) -> None:
        if not tenant_id:
            raise ValueError("tenant_id is required")
        async with memory_repositories._lock:
            object.__setattr__(event, 'tenant_id', tenant_id)
            memory_repositories.audit_events.append(event)

    async def list_recent(self, tenant_id: str = "default", limit: int = 100, bypass_tenant: bool = False) -> List[AuditEvent]:
        if isinstance(tenant_id, int):
            limit = tenant_id
            tenant_id = "default"
        if not tenant_id:
            tenant_id = "default"
        if not bypass_tenant and not tenant_id:
            raise ValueError("tenant_id is required")
        async with memory_repositories._lock:
            res = []
            for event in memory_repositories.audit_events:
                if _check_tenant(event, tenant_id, bypass_tenant, "list_audits", f"audit_event:{event.id}"):
                    res.append(event)
            return sorted(res, key=lambda e: e.created_at, reverse=True)[:limit]


@compatibility_class_decorator
class InMemoryWebhookDeliveryRepository(WebhookDeliveryRepository):
    async def log_delivery(self, delivery_data: Dict[str, Any], tenant_id: str = "default") -> None:
        if not tenant_id:
            tenant_id = "default"
        async with memory_repositories._lock:
            data = delivery_data.copy()
            if "id" not in data:
                data["id"] = f"web_{uuid.uuid4().hex[:8]}"
            if "created_at" not in data:
                data["created_at"] = datetime.now(timezone.utc)
            data["tenant_id"] = tenant_id
            memory_repositories.webhook_deliveries.append(data)

    async def create_delivery(self, delivery_data: Dict[str, Any], tenant_id: str = "default") -> Dict[str, Any]:
        if not tenant_id:
            tenant_id = "default"
        async with memory_repositories._lock:
            data = delivery_data.copy()
            data["id"] = f"web_{uuid.uuid4().hex[:8]}"
            data["created_at"] = datetime.now(timezone.utc)
            data["tenant_id"] = tenant_id
            memory_repositories.webhook_deliveries.append(data)
            return data

    async def update_delivery(self, delivery_id: str, delivery_status: str, status_code: Optional[float], error_message: Optional[str], attempt_count: float, tenant_id: str = "default", bypass_tenant: bool = False) -> Optional[Dict[str, Any]]:
        if not tenant_id:
            tenant_id = "default"
        async with memory_repositories._lock:
            for item in memory_repositories.webhook_deliveries:
                if item.get("id") == delivery_id:
                    if not _check_tenant(item, tenant_id, bypass_tenant, "update_delivery", f"webhook_delivery:{delivery_id}"):
                        return None
                    item["delivery_status"] = delivery_status
                    item["status_code"] = status_code
                    item["error_message"] = error_message
                    item["attempt_count"] = attempt_count
                    return item
            return None

    async def get_delivery(self, delivery_id: str, tenant_id: str = "default", bypass_tenant: bool = False) -> Optional[Dict[str, Any]]:
        if tenant_id is None or isinstance(tenant_id, bool):
            actual_bypass = tenant_id if isinstance(tenant_id, bool) else bypass_tenant
            tenant_id = "default"
            bypass_tenant = actual_bypass
        async with memory_repositories._lock:
            for item in memory_repositories.webhook_deliveries:
                if item.get("id") == delivery_id:
                    if not _check_tenant(item, tenant_id, bypass_tenant, "get_delivery", f"webhook_delivery:{delivery_id}"):
                        return None
                    return item
            return None

    async def list_deliveries(self, tenant_id: str = "default", bypass_tenant: bool = False) -> List[Dict[str, Any]]:
        if not tenant_id:
            tenant_id = "default"
        if not bypass_tenant and not tenant_id:
            raise ValueError("tenant_id is required")
        async with memory_repositories._lock:
            res = []
            for item in memory_repositories.webhook_deliveries:
                if _check_tenant(item, tenant_id, bypass_tenant, "list_deliveries", f"webhook_delivery:{item.get('id')}"):
                    res.append(item)
            return sorted(res, key=lambda d: d.get("created_at") or datetime.min.replace(tzinfo=timezone.utc), reverse=True)


@compatibility_class_decorator
class InMemoryReleaseCheckRepository(ReleaseCheckRepository):
    async def create_check(self, check_data: Dict[str, Any]) -> Dict[str, Any]:
        async with memory_repositories._lock:
            check_data = check_data.copy()
            if "id" not in check_data:
                check_data["id"] = f"rel_{uuid.uuid4().hex[:8]}"
            if "created_at" not in check_data:
                check_data["created_at"] = datetime.now(timezone.utc)
            memory_repositories.release_checks.append(check_data)
            return check_data

    async def get_latest_check(self) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            if not memory_repositories.release_checks:
                return None
            sorted_checks = sorted(memory_repositories.release_checks, key=lambda c: c.get("created_at"), reverse=True)
            return sorted_checks[0]

    async def list_checks(self, limit: int = 20) -> List[Dict[str, Any]]:
        async with memory_repositories._lock:
            sorted_checks = sorted(memory_repositories.release_checks, key=lambda c: c.get("created_at"), reverse=True)
            return sorted_checks[:limit]


@compatibility_class_decorator
class InMemoryApiKeyRepository(ApiKeyRepository):
    async def create(self, key_data: Dict[str, Any]) -> Dict[str, Any]:
        async with memory_repositories._lock:
            key_data = key_data.copy()
            key_id = key_data.get("id") or f"key_{uuid.uuid4().hex[:8]}"
            key_data["id"] = key_id
            key_data["created_at"] = datetime.now(timezone.utc)
            memory_repositories.api_keys[key_id] = key_data
            return key_data

    async def get(self, key_id: str) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            return memory_repositories.api_keys.get(key_id)

    async def get_by_hash(self, key_hash: str) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            for k in memory_repositories.api_keys.values():
                if k.get("key_hash") == key_hash:
                    return k
            return None

    async def list_all(self) -> List[Dict[str, Any]]:
        async with memory_repositories._lock:
            return list(memory_repositories.api_keys.values())

    async def revoke(self, key_id: str, revoked_by: str, reason: str) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            if key_id not in memory_repositories.api_keys:
                return None
            key = memory_repositories.api_keys[key_id]
            key["is_active"] = False
            key["revoked_by"] = revoked_by
            key["revoke_reason"] = reason
            key["revoked_at"] = datetime.now(timezone.utc)
            return key

    async def update_last_used(self, key_id: str, last_used: datetime) -> None:
        async with memory_repositories._lock:
            if key_id in memory_repositories.api_keys:
                memory_repositories.api_keys[key_id]["last_used_at"] = last_used

    async def update_quota(self, key_id: str, quota_daily: Optional[int], quota_monthly: Optional[int]) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            if key_id not in memory_repositories.api_keys:
                return None
            key = memory_repositories.api_keys[key_id]
            key["quota_daily"] = quota_daily
            key["quota_monthly"] = quota_monthly
            return key


@compatibility_class_decorator
class InMemoryResearchRepository(ResearchRepository):
    async def create_request(self, request_data: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
        if not tenant_id:
            raise ValueError("tenant_id is required")
        async with memory_repositories._lock:
            req_id = request_data.get("id") or f"res_{uuid.uuid4().hex[:8]}"
            req = request_data.copy()
            req["id"] = req_id
            req["tenant_id"] = tenant_id
            req["status"] = request_data.get("status", "PENDING")
            req["created_at"] = datetime.now(timezone.utc)
            memory_repositories.research_requests[req_id] = req
            return req

    async def get_request(self, request_id: str, tenant_id: str, bypass_tenant: bool = False) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            obj = memory_repositories.research_requests.get(request_id)
            if not obj:
                return None
            if not _check_tenant(obj, tenant_id, bypass_tenant, "get_request", f"research_request:{request_id}"):
                return None
            return obj

    async def update_request_status(self, request_id: str, status: str, tenant_id: str, error_message: Optional[str] = None, bypass_tenant: bool = False) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            obj = memory_repositories.research_requests.get(request_id)
            if not obj:
                return None
            if not _check_tenant(obj, tenant_id, bypass_tenant, "update_request_status", f"research_request:{request_id}"):
                return None
            obj["status"] = status
            obj["error_message"] = error_message
            obj["updated_at"] = datetime.now(timezone.utc)
            return obj

    async def create_evidence(self, evidence_data: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
        if not tenant_id:
            raise ValueError("tenant_id is required")
        # Enforce that parent research request belongs to tenant
        research_id = evidence_data.get("research_id")
        await self.get_request(research_id, tenant_id) # Raises or returns None (OLA)
        async with memory_repositories._lock:
            ev_id = f"evd_{uuid.uuid4().hex[:8]}"
            ev = evidence_data.copy()
            ev["id"] = ev_id
            ev["tenant_id"] = tenant_id
            ev["trust_score"] = evidence_data.get("trust_score", 0.0)
            ev["retrieved_at"] = datetime.now(timezone.utc)
            memory_repositories.research_evidences[ev_id] = ev
            return ev

    async def list_evidences(self, research_id: str, tenant_id: str, bypass_tenant: bool = False) -> List[Dict[str, Any]]:
        # Enforce research request is owned by tenant
        await self.get_request(research_id, tenant_id, bypass_tenant)
        async with memory_repositories._lock:
            res = []
            for ev in memory_repositories.research_evidences.values():
                if ev.get("research_id") == research_id:
                    if _check_tenant(ev, tenant_id, bypass_tenant, "list_evidences", f"evidence:{ev.get('id')}"):
                        res.append(ev)
            return res

    async def get_tenant_daily_research_count(self, tenant_id: str = "default", day: Optional[datetime] = None) -> int:
        if isinstance(tenant_id, datetime):
            day = tenant_id
            tenant_id = "default"
        if not tenant_id:
            tenant_id = "default"
        if not day:
            day = datetime.now(timezone.utc)
        async with memory_repositories._lock:
            count = 0
            for req in memory_repositories.research_requests.values():
                req_tenant = req.get("tenant_id") or "default"
                if req_tenant == tenant_id:
                    created_at = req.get("created_at")
                    if created_at and created_at.date() == day.date():
                        count += 1
            return count


@compatibility_class_decorator
class InMemoryImprovementRepository(ImprovementRepository):
    async def create_proposal(self, proposal_data: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
        if not tenant_id:
            raise ValueError("tenant_id is required")
        async with memory_repositories._lock:
            prop_id = f"prp_{uuid.uuid4().hex[:8]}"
            prop = proposal_data.copy()
            prop["id"] = prop_id
            prop["tenant_id"] = tenant_id
            prop["created_at"] = datetime.now(timezone.utc)
            prop["updated_at"] = datetime.now(timezone.utc)
            memory_repositories.improvement_proposals[prop_id] = prop
            return prop

    async def get_proposal(self, proposal_id: str, tenant_id: str, bypass_tenant: bool = False) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            obj = memory_repositories.improvement_proposals.get(proposal_id)
            if not obj:
                return None
            if not _check_tenant(obj, tenant_id, bypass_tenant, "get_proposal", f"improvement_proposal:{proposal_id}"):
                return None
            return obj

    async def update_proposal_gate(self, proposal_id: str, gate_status: str, tenant_id: str, gate_score: Optional[float] = None, risk_analysis: Optional[Dict[str, Any]] = None, approval_status: Optional[str] = None, bypass_tenant: bool = False) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            obj = memory_repositories.improvement_proposals.get(proposal_id)
            if not obj:
                return None
            if not _check_tenant(obj, tenant_id, bypass_tenant, "update_proposal_gate", f"improvement_proposal:{proposal_id}"):
                return None
            obj["gate_status"] = gate_status
            if gate_score is not None:
                obj["gate_score"] = gate_score
            if risk_analysis is not None:
                obj["risk_analysis"] = risk_analysis
            if approval_status is not None:
                obj["approval_status"] = approval_status
            obj["updated_at"] = datetime.now(timezone.utc)
            return obj

    async def approve_proposal(self, proposal_id: str, approved_by: str, approved_at: datetime, tenant_id: str, bypass_tenant: bool = False) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            obj = memory_repositories.improvement_proposals.get(proposal_id)
            if not obj:
                return None
            if not _check_tenant(obj, tenant_id, bypass_tenant, "approve_proposal", f"improvement_proposal:{proposal_id}"):
                return None
            obj["approval_status"] = "APPROVED"
            obj["approved_by"] = approved_by
            obj["approved_at"] = approved_at
            obj["ready_for_human_apply"] = True
            obj["updated_at"] = datetime.now(timezone.utc)
            return obj

    async def list_proposals(self, tenant_id: str, bypass_tenant: bool = False) -> List[Dict[str, Any]]:
        if not bypass_tenant and not tenant_id:
            raise ValueError("tenant_id is required")
        async with memory_repositories._lock:
            res = []
            for obj in memory_repositories.improvement_proposals.values():
                if _check_tenant(obj, tenant_id, bypass_tenant, "list_proposals", f"improvement_proposal:{obj.get('id')}"):
                    res.append(obj)
            return sorted(res, key=lambda x: x.get("created_at") or datetime.min.replace(tzinfo=timezone.utc), reverse=True)


@compatibility_class_decorator
class InMemoryPrDraftRepository(PrDraftRepository):
    async def create_pr_draft(self, draft_data: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
        if not tenant_id:
            raise ValueError("tenant_id is required")
        async with memory_repositories._lock:
            draft_id = f"prd_{uuid.uuid4().hex[:8]}"
            draft = draft_data.copy()
            draft["id"] = draft_id
            draft["tenant_id"] = tenant_id
            draft["created_at"] = datetime.now(timezone.utc)
            draft["updated_at"] = datetime.now(timezone.utc)
            memory_repositories.pr_drafts[draft_id] = draft
            return draft

    async def get_pr_draft(self, draft_id: str, tenant_id: str, bypass_tenant: bool = False) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            obj = memory_repositories.pr_drafts.get(draft_id)
            if not obj:
                return None
            if not _check_tenant(obj, tenant_id, bypass_tenant, "get_pr_draft", f"pr_draft:{draft_id}"):
                return None
            return obj

    async def list_pr_drafts_by_proposal(self, proposal_id: str, tenant_id: str, bypass_tenant: bool = False) -> List[Dict[str, Any]]:
        if not bypass_tenant and not tenant_id:
            raise ValueError("tenant_id is required")
        async with memory_repositories._lock:
            res = []
            for d in memory_repositories.pr_drafts.values():
                if d.get("proposal_id") == proposal_id:
                    if _check_tenant(d, tenant_id, bypass_tenant, "list_pr_drafts", f"pr_draft:{d.get('id')}"):
                        res.append(d)
            return res

    async def update_pr_draft_status(self, draft_id: str, status: str, tenant_id: str, github_pr_url: Optional[str] = None, error_message: Optional[str] = None, bypass_tenant: bool = False) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            obj = memory_repositories.pr_drafts.get(draft_id)
            if not obj:
                return None
            if not _check_tenant(obj, tenant_id, bypass_tenant, "update_pr_draft_status", f"pr_draft:{draft_id}"):
                return None
            obj["status"] = status
            if github_pr_url:
                obj["github_pr_url"] = github_pr_url
            if error_message:
                obj["error_message"] = error_message
            obj["updated_at"] = datetime.now(timezone.utc)
            return obj


@compatibility_class_decorator
class InMemoryPrVerificationRepository(PrVerificationRepository):
    async def create_verification(self, verification_data: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
        if not tenant_id:
            raise ValueError("tenant_id is required")
        async with memory_repositories._lock:
            v_id = f"ver_{uuid.uuid4().hex[:8]}"
            ver = verification_data.copy()
            ver["id"] = v_id
            ver["tenant_id"] = tenant_id
            ver["created_at"] = datetime.now(timezone.utc)
            ver["updated_at"] = datetime.now(timezone.utc)
            memory_repositories.pr_verifications[v_id] = ver
            return ver

    async def get_verification_by_pr_draft(self, pr_draft_id: str, tenant_id: str, bypass_tenant: bool = False) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            for v in memory_repositories.pr_verifications.values():
                if v.get("pr_draft_id") == pr_draft_id:
                    if not _check_tenant(v, tenant_id, bypass_tenant, "get_verification", f"pr_verification:{v.get('id')}"):
                        return None
                    return v
            return None

    async def list_verifications_by_proposal(self, proposal_id: str, tenant_id: str, bypass_tenant: bool = False) -> List[Dict[str, Any]]:
        if not bypass_tenant and not tenant_id:
            raise ValueError("tenant_id is required")
        async with memory_repositories._lock:
            res = []
            for v in memory_repositories.pr_verifications.values():
                if v.get("proposal_id") == proposal_id:
                    if _check_tenant(v, tenant_id, bypass_tenant, "list_verifications", f"pr_verification:{v.get('id')}"):
                        res.append(v)
            return res

    async def get_verification_by_revision(self, revision_id: str, tenant_id: str, bypass_tenant: bool = False) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            for v in memory_repositories.pr_verifications.values():
                if v.get("revision_id") == revision_id:
                    if not _check_tenant(v, tenant_id, bypass_tenant, "get_verification", f"pr_verification:{v.get('id')}"):
                        return None
                    return v
            return None

    async def get_verification_by_ai_suggestion(self, suggestion_id: str, tenant_id: str, bypass_tenant: bool = False) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            for v in memory_repositories.pr_verifications.values():
                if v.get("ai_suggestion_id") == suggestion_id:
                    if not _check_tenant(v, tenant_id, bypass_tenant, "get_verification", f"pr_verification:{v.get('id')}"):
                        return None
                    return v
            return None


@compatibility_class_decorator
class InMemoryPrReviewFeedbackRepository(PrReviewFeedbackRepository):
    async def create_feedback(self, feedback_data: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
        if not tenant_id:
            raise ValueError("tenant_id is required")
        async with memory_repositories._lock:
            fb_id = f"fdb_{uuid.uuid4().hex[:8]}"
            fb = feedback_data.copy()
            fb["id"] = fb_id
            fb["tenant_id"] = tenant_id
            fb["created_at"] = datetime.now(timezone.utc)
            fb["updated_at"] = datetime.now(timezone.utc)
            memory_repositories.pr_review_feedbacks[fb_id] = fb
            return fb

    async def get_feedback(self, feedback_id: str, tenant_id: str, bypass_tenant: bool = False) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            obj = memory_repositories.pr_review_feedbacks.get(feedback_id)
            if not obj:
                return None
            if not _check_tenant(obj, tenant_id, bypass_tenant, "get_feedback", f"pr_feedback:{feedback_id}"):
                return None
            return obj

    async def list_feedback_by_pr_draft(self, pr_draft_id: str, tenant_id: str, bypass_tenant: bool = False) -> List[Dict[str, Any]]:
        if not bypass_tenant and not tenant_id:
            raise ValueError("tenant_id is required")
        async with memory_repositories._lock:
            res = []
            for f in memory_repositories.pr_review_feedbacks.values():
                if f.get("pr_draft_id") == pr_draft_id:
                    if _check_tenant(f, tenant_id, bypass_tenant, "list_feedback", f"pr_feedback:{f.get('id')}"):
                        res.append(f)
            return res

    async def update_feedback_status(self, feedback_id: str, status: str, tenant_id: str, bypass_tenant: bool = False) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            obj = memory_repositories.pr_review_feedbacks.get(feedback_id)
            if not obj:
                return None
            if not _check_tenant(obj, tenant_id, bypass_tenant, "update_feedback", f"pr_feedback:{feedback_id}"):
                return None
            obj["status"] = status
            obj["updated_at"] = datetime.now(timezone.utc)
            return obj


@compatibility_class_decorator
class InMemoryPatchRevisionRepository(PatchRevisionRepository):
    async def create_revision(self, revision_data: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
        if not tenant_id:
            raise ValueError("tenant_id is required")
        async with memory_repositories._lock:
            rev_id = f"rev_{uuid.uuid4().hex[:8]}"
            rev = revision_data.copy()
            rev["id"] = rev_id
            rev["tenant_id"] = tenant_id
            rev["created_at"] = datetime.now(timezone.utc)
            rev["updated_at"] = datetime.now(timezone.utc)
            memory_repositories.patch_revisions[rev_id] = rev
            return rev

    async def get_revision(self, revision_id: str, tenant_id: str, bypass_tenant: bool = False) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            obj = memory_repositories.patch_revisions.get(revision_id)
            if not obj:
                return None
            if not _check_tenant(obj, tenant_id, bypass_tenant, "get_revision", f"patch_revision:{revision_id}"):
                return None
            return obj

    async def get_latest_revision_number(self, pr_draft_id: str, tenant_id: str, bypass_tenant: bool = False) -> int:
        if not bypass_tenant and not tenant_id:
            raise ValueError("tenant_id is required")
        async with memory_repositories._lock:
            nums = []
            for rev in memory_repositories.patch_revisions.values():
                if rev.get("pr_draft_id") == pr_draft_id:
                    if _check_tenant(rev, tenant_id, bypass_tenant, "get_latest_rev", f"pr_draft:{pr_draft_id}"):
                        nums.append(rev.get("revision_number", 0))
            return max(nums) if nums else 0

    async def list_revisions_by_pr_draft(self, pr_draft_id: str, tenant_id: str, bypass_tenant: bool = False) -> List[Dict[str, Any]]:
        if not bypass_tenant and not tenant_id:
            raise ValueError("tenant_id is required")
        async with memory_repositories._lock:
            res = []
            for rev in memory_repositories.patch_revisions.values():
                if rev.get("pr_draft_id") == pr_draft_id:
                    if _check_tenant(rev, tenant_id, bypass_tenant, "list_revisions", f"pr_draft:{pr_draft_id}"):
                        res.append(rev)
            return sorted(res, key=lambda r: r.get("revision_number", 0), reverse=True)

    async def update_verification_status(self, revision_id: str, status: str, tenant_id: str, bypass_tenant: bool = False) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            obj = memory_repositories.patch_revisions.get(revision_id)
            if not obj:
                return None
            if not _check_tenant(obj, tenant_id, bypass_tenant, "update_revision", f"patch_revision:{revision_id}"):
                return None
            obj["verification_status"] = status
            obj["updated_at"] = datetime.now(timezone.utc)
            return obj


@compatibility_class_decorator
class InMemoryReviewLedgerRepository(ReviewLedgerRepository):
    async def append_entry(self, entry_data: Dict[str, Any], tenant_id: str = "default") -> Dict[str, Any]:
        if not tenant_id:
            tenant_id = "default"
        async with memory_repositories._lock:
            entry_id = entry_data.get("id") or f"led_{uuid.uuid4().hex[:8]}"
            entry = entry_data.copy()
            entry["id"] = entry_id
            entry["tenant_id"] = tenant_id
            if "created_at" not in entry or entry["created_at"] is None:
                entry["created_at"] = datetime.now(timezone.utc)
            memory_repositories.review_ledger_entries[entry_id] = entry
            return entry

    async def get_entry(self, entry_id: str, tenant_id: str = "default", bypass_tenant: bool = False) -> Optional[Dict[str, Any]]:
        if isinstance(tenant_id, bool):
            bypass_tenant = tenant_id
            tenant_id = "default"
        if not tenant_id:
            tenant_id = "default"
        async with memory_repositories._lock:
            obj = memory_repositories.review_ledger_entries.get(entry_id)
            if not obj:
                return None
            if not _check_tenant(obj, tenant_id, bypass_tenant, "get_entry", f"ledger_entry:{entry_id}"):
                return None
            return obj

    async def get_latest_entry(self, chain_id: str, tenant_id: str = "default", bypass_tenant: bool = False) -> Optional[Dict[str, Any]]:
        if isinstance(tenant_id, bool):
            bypass_tenant = tenant_id
            tenant_id = "default"
        if not tenant_id:
            tenant_id = "default"
        if not bypass_tenant and not tenant_id:
            raise ValueError("tenant_id is required")
        async with memory_repositories._lock:
            entries = []
            for e in memory_repositories.review_ledger_entries.values():
                if e.get("chain_id") == chain_id:
                    if _check_tenant(e, tenant_id, bypass_tenant, "get_latest_entry", f"ledger_chain:{chain_id}"):
                        entries.append(e)
            if not entries:
                return None
            return sorted(entries, key=lambda x: x.get("sequence_no", 0), reverse=True)[0]

    async def list_by_chain(self, chain_id: str, tenant_id: str = "default", bypass_tenant: bool = False) -> List[Dict[str, Any]]:
        if isinstance(tenant_id, bool):
            bypass_tenant = tenant_id
            tenant_id = "default"
        if not tenant_id:
            tenant_id = "default"
        if not bypass_tenant and not tenant_id:
            raise ValueError("tenant_id is required")
        async with memory_repositories._lock:
            entries = []
            for e in memory_repositories.review_ledger_entries.values():
                if e.get("chain_id") == chain_id:
                    if _check_tenant(e, tenant_id, bypass_tenant, "list_ledger", f"ledger_chain:{chain_id}"):
                        entries.append(e)
            return sorted(entries, key=lambda x: x.get("sequence_no", 0))

    async def list_recent(self, tenant_id: str = "default", limit: int = 50, bypass_tenant: bool = False) -> List[Dict[str, Any]]:
        if isinstance(tenant_id, bool):
            bypass_tenant = tenant_id
            tenant_id = "default"
        elif isinstance(tenant_id, int):
            if isinstance(limit, bool):
                bypass_tenant = limit
                limit = tenant_id
            else:
                limit = tenant_id
            tenant_id = "default"
        if not tenant_id:
            tenant_id = "default"
        if not bypass_tenant and not tenant_id:
            raise ValueError("tenant_id is required")
        async with memory_repositories._lock:
            res = []
            for e in memory_repositories.review_ledger_entries.values():
                if _check_tenant(e, tenant_id, bypass_tenant, "list_recent_ledger", "ledger"):
                    res.append(e)
            return sorted(res, key=lambda x: x.get("created_at") or datetime.min.replace(tzinfo=timezone.utc), reverse=True)[:limit]


@compatibility_class_decorator
class InMemoryAIPatchSuggestionRepository(AIPatchSuggestionRepository):
    async def create_suggestion(self, data: Dict[str, Any], tenant_id: str = "default") -> Dict[str, Any]:
        if not tenant_id:
            tenant_id = "default"
        async with memory_repositories._lock:
            s_id = f"sug_{uuid.uuid4().hex[:8]}"
            sug = data.copy()
            sug["id"] = s_id
            sug["tenant_id"] = tenant_id
            sug["created_at"] = datetime.now(timezone.utc)
            sug["updated_at"] = datetime.now(timezone.utc)
            memory_repositories.ai_patch_suggestions[s_id] = sug
            return sug

    async def get_suggestion(self, suggestion_id: str, tenant_id: str = "default", bypass_tenant: bool = False) -> Optional[Dict[str, Any]]:
        if isinstance(tenant_id, bool):
            bypass_tenant = tenant_id
            tenant_id = "default"
        if not tenant_id:
            tenant_id = "default"
        async with memory_repositories._lock:
            obj = memory_repositories.ai_patch_suggestions.get(suggestion_id)
            if not obj:
                return None
            if not _check_tenant(obj, tenant_id, bypass_tenant, "get_suggestion", f"suggestion:{suggestion_id}"):
                return None
            return obj

    async def list_suggestions_by_pr_draft(self, pr_draft_id: str, tenant_id: str = "default", bypass_tenant: bool = False) -> List[Dict[str, Any]]:
        if isinstance(tenant_id, bool):
            bypass_tenant = tenant_id
            tenant_id = "default"
        if not tenant_id:
            tenant_id = "default"
        if not bypass_tenant and not tenant_id:
            raise ValueError("tenant_id is required")
        async with memory_repositories._lock:
            res = []
            for s in memory_repositories.ai_patch_suggestions.values():
                if s.get("pr_draft_id") == pr_draft_id:
                    if _check_tenant(s, tenant_id, bypass_tenant, "list_suggestions", f"pr_draft:{pr_draft_id}"):
                        res.append(s)
            return res

    async def update_suggestion_status(self, suggestion_id: str, status: str, tenant_id: str = "default", bypass_tenant: bool = False) -> Optional[Dict[str, Any]]:
        if isinstance(tenant_id, bool):
            bypass_tenant = tenant_id
            tenant_id = "default"
        if not tenant_id:
            tenant_id = "default"
        async with memory_repositories._lock:
            obj = memory_repositories.ai_patch_suggestions.get(suggestion_id)
            if not obj:
                return None
            if not _check_tenant(obj, tenant_id, bypass_tenant, "update_suggestion", f"suggestion:{suggestion_id}"):
                return None
            obj["status"] = status
            obj["updated_at"] = datetime.now(timezone.utc)
            return obj

    async def attach_verification(self, suggestion_id: str, verification_id: str, risk_level: str, status: str, tenant_id: str = "default", bypass_tenant: bool = False) -> Optional[Dict[str, Any]]:
        if isinstance(tenant_id, bool):
            bypass_tenant = tenant_id
            tenant_id = "default"
        if not tenant_id:
            tenant_id = "default"
        async with memory_repositories._lock:
            obj = memory_repositories.ai_patch_suggestions.get(suggestion_id)
            if not obj:
                return None
            if not _check_tenant(obj, tenant_id, bypass_tenant, "attach_verification", f"suggestion:{suggestion_id}"):
                return None
            obj["verification_id"] = verification_id
            obj["risk_level"] = risk_level
            obj["status"] = status
            obj["updated_at"] = datetime.now(timezone.utc)
            return obj


@compatibility_class_decorator
class InMemorySystemFindingRepository(SystemFindingRepository):
    async def create_finding(self, finding_data: Dict[str, Any], tenant_id: str = "default") -> Dict[str, Any]:
        if not tenant_id:
            tenant_id = "default"
        async with memory_repositories._lock:
            f_id = finding_data.get("id") or f"sfnd_{uuid.uuid4().hex[:8]}"
            finding = finding_data.copy()
            finding["id"] = f_id
            finding["tenant_id"] = tenant_id
            finding["occurrence_count"] = finding.get("occurrence_count", 1)
            finding["first_seen_at"] = datetime.now(timezone.utc)
            finding["last_seen_at"] = datetime.now(timezone.utc)
            finding["created_at"] = datetime.now(timezone.utc)
            finding["updated_at"] = datetime.now(timezone.utc)
            memory_repositories.system_findings[f_id] = finding
            return finding

    async def get_finding(self, finding_id: str, tenant_id: str = "default", bypass_tenant: bool = False) -> Optional[Dict[str, Any]]:
        if isinstance(tenant_id, bool):
            bypass_tenant = tenant_id
            tenant_id = "default"
        if not tenant_id:
            tenant_id = "default"
        async with memory_repositories._lock:
            obj = memory_repositories.system_findings.get(finding_id)
            if not obj:
                return None
            if not _check_tenant(obj, tenant_id, bypass_tenant, "get_finding", f"system_finding:{finding_id}"):
                return None
            return obj

    async def get_open_by_source_hash(self, source_hash: str, tenant_id: str = "default", bypass_tenant: bool = False) -> Optional[Dict[str, Any]]:
        if isinstance(tenant_id, bool):
            bypass_tenant = tenant_id
            tenant_id = "default"
        if not tenant_id:
            tenant_id = "default"
        if not bypass_tenant and not tenant_id:
            raise ValueError("tenant_id is required")
        async with memory_repositories._lock:
            for f in memory_repositories.system_findings.values():
                if f.get("source_hash") == source_hash and f.get("status") == "OPEN":
                    if not _check_tenant(f, tenant_id, bypass_tenant, "get_finding_hash", f"finding_hash:{source_hash}"):
                        return None
                    return f
            return None

    async def get_by_source_hash(self, source_hash: str, tenant_id: str = "default", bypass_tenant: bool = False) -> Optional[Dict[str, Any]]:
        if isinstance(tenant_id, bool):
            bypass_tenant = tenant_id
            tenant_id = "default"
        if not tenant_id:
            tenant_id = "default"
        if not bypass_tenant and not tenant_id:
            raise ValueError("tenant_id is required")
        async with memory_repositories._lock:
            for f in memory_repositories.system_findings.values():
                if f.get("source_hash") == source_hash:
                    if not _check_tenant(f, tenant_id, bypass_tenant, "get_finding_hash", f"finding_hash:{source_hash}"):
                        return None
                    return f
            return None

    async def list_findings(self, tenant_id: str = "default", status: Optional[str] = None, severity: Optional[str] = None, limit: int = 50, bypass_tenant: bool = False) -> List[Dict[str, Any]]:
        if isinstance(tenant_id, bool):
            bypass_tenant = tenant_id
            tenant_id = "default"
        elif isinstance(tenant_id, int):
            limit = tenant_id
            tenant_id = "default"
        if not tenant_id:
            tenant_id = "default"
        if not bypass_tenant and not tenant_id:
            raise ValueError("tenant_id is required")
        async with memory_repositories._lock:
            res = []
            for f in memory_repositories.system_findings.values():
                if _check_tenant(f, tenant_id, bypass_tenant, "list_findings", "system_findings"):
                    if status and f.get("status") != status:
                        continue
                    if severity and f.get("severity") != severity:
                        continue
                    res.append(f)
            return sorted(res, key=lambda x: x.get("created_at") or datetime.min.replace(tzinfo=timezone.utc), reverse=True)[:limit]

    async def increment_occurrence(self, finding_id: str, tenant_id: str = "default", evidence_summary: Optional[Dict[str, Any]] = None, bypass_tenant: bool = False) -> Optional[Dict[str, Any]]:
        if isinstance(tenant_id, dict):
            evidence_summary = tenant_id
            tenant_id = "default"
        elif isinstance(tenant_id, bool):
            bypass_tenant = tenant_id
            tenant_id = "default"
        if not tenant_id:
            tenant_id = "default"
        async with memory_repositories._lock:
            obj = memory_repositories.system_findings.get(finding_id)
            if not obj:
                return None
            if not _check_tenant(obj, tenant_id, bypass_tenant, "increment_occurrence", f"system_finding:{finding_id}"):
                return None
            obj["occurrence_count"] = obj.get("occurrence_count", 1) + 1
            obj["last_seen_at"] = datetime.now(timezone.utc)
            if evidence_summary:
                obj["evidence_summary"] = evidence_summary
            return obj

    async def update_status(self, finding_id: str, status: str, actor_id: str, tenant_id: str = "default", bypass_tenant: bool = False) -> Optional[Dict[str, Any]]:
        if isinstance(tenant_id, bool):
            bypass_tenant = tenant_id
            tenant_id = "default"
        if not tenant_id:
            tenant_id = "default"
        async with memory_repositories._lock:
            obj = memory_repositories.system_findings.get(finding_id)
            if not obj:
                return None
            if not _check_tenant(obj, tenant_id, bypass_tenant, "update_status", f"system_finding:{finding_id}"):
                return None
            obj["status"] = status
            if status == "ACKNOWLEDGED":
                obj["acknowledged_by"] = actor_id
                obj["acknowledged_at"] = datetime.now(timezone.utc)
            elif status == "DISMISSED":
                obj["dismissed_by"] = actor_id
                obj["dismissed_at"] = datetime.now(timezone.utc)
            elif status == "RESOLVED":
                obj["resolved_by"] = actor_id
                obj["resolved_at"] = datetime.now(timezone.utc)
            obj["updated_at"] = datetime.now(timezone.utc)
            return obj


@compatibility_class_decorator
class InMemoryRemediationRunbookRepository(RemediationRunbookRepository):
    async def create_runbook(self, runbook_data: Dict[str, Any], tenant_id: str = "default") -> Dict[str, Any]:
        if not tenant_id:
            tenant_id = "default"
        async with memory_repositories._lock:
            rb_id = f"rb_{uuid.uuid4().hex[:8]}"
            rb = runbook_data.copy()
            rb["id"] = rb_id
            rb["tenant_id"] = tenant_id
            rb["created_at"] = datetime.now(timezone.utc)
            rb["updated_at"] = datetime.now(timezone.utc)
            memory_repositories.remediation_runbooks = getattr(memory_repositories, "remediation_runbooks", {})
            memory_repositories.remediation_runbooks[rb_id] = rb
            return rb

    async def get_runbook(self, runbook_id: str, tenant_id: str = "default", bypass_tenant: bool = False) -> Optional[Dict[str, Any]]:
        if isinstance(tenant_id, bool):
            bypass_tenant = tenant_id
            tenant_id = "default"
        if not tenant_id:
            tenant_id = "default"
        async with memory_repositories._lock:
            obj = memory_repositories.remediation_runbooks.get(runbook_id)
            if not obj:
                return None
            if not _check_tenant(obj, tenant_id, bypass_tenant, "get_runbook", f"runbook:{runbook_id}"):
                return None
            return obj

    async def get_runbook_by_name(self, name: str, tenant_id: str = "default", bypass_tenant: bool = False) -> Optional[Dict[str, Any]]:
        if isinstance(tenant_id, bool):
            bypass_tenant = tenant_id
            tenant_id = "default"
        if not tenant_id:
            tenant_id = "default"
        if not bypass_tenant and not tenant_id:
            raise ValueError("tenant_id is required")
        async with memory_repositories._lock:
            for r in memory_repositories.remediation_runbooks.values():
                if r.get("name") == name:
                    if not _check_tenant(r, tenant_id, bypass_tenant, "get_runbook_name", f"runbook_name:{name}"):
                        return None
                    return r
            return None

    async def list_runbooks(self, tenant_id: str = "default", bypass_tenant: bool = False) -> List[Dict[str, Any]]:
        if isinstance(tenant_id, bool):
            bypass_tenant = tenant_id
            tenant_id = "default"
        if not tenant_id:
            tenant_id = "default"
        if not bypass_tenant and not tenant_id:
            raise ValueError("tenant_id is required")
        async with memory_repositories._lock:
            res = []
            for r in memory_repositories.remediation_runbooks.values():
                if _check_tenant(r, tenant_id, bypass_tenant, "list_runbooks", "runbooks"):
                    res.append(r)
            return res

    async def update_runbook_enabled(self, runbook_id: str, enabled: bool, tenant_id: str = "default", bypass_tenant: bool = False) -> Optional[Dict[str, Any]]:
        if isinstance(tenant_id, bool):
            bypass_tenant = tenant_id
            tenant_id = "default"
        if not tenant_id:
            tenant_id = "default"
        async with memory_repositories._lock:
            obj = memory_repositories.remediation_runbooks.get(runbook_id)
            if not obj:
                return None
            if not _check_tenant(obj, tenant_id, bypass_tenant, "update_runbook", f"runbook:{runbook_id}"):
                return None
            obj["enabled"] = enabled
            obj["updated_at"] = datetime.now(timezone.utc)
            return obj


@compatibility_class_decorator
class InMemoryRemediationAttemptRepository(RemediationAttemptRepository):
    async def create_attempt(self, attempt_data: Dict[str, Any], tenant_id: str = "default") -> Dict[str, Any]:
        if not tenant_id:
            tenant_id = "default"
        async with memory_repositories._lock:
            att_id = f"att_{uuid.uuid4().hex[:8]}"
            att = attempt_data.copy()
            att["id"] = att_id
            att["tenant_id"] = tenant_id
            att["created_at"] = datetime.now(timezone.utc)
            att["updated_at"] = datetime.now(timezone.utc)
            memory_repositories.remediation_attempts[att_id] = att
            return att

    async def get_attempt(self, attempt_id: str, tenant_id: str = "default", bypass_tenant: bool = False) -> Optional[Dict[str, Any]]:
        if isinstance(tenant_id, bool):
            bypass_tenant = tenant_id
            tenant_id = "default"
        if not tenant_id:
            tenant_id = "default"
        async with memory_repositories._lock:
            obj = memory_repositories.remediation_attempts.get(attempt_id)
            if not obj:
                return None
            if not _check_tenant(obj, tenant_id, bypass_tenant, "get_attempt", f"remediation_attempt:{attempt_id}"):
                return None
            return obj

    async def list_attempts_by_finding(self, finding_id: str, tenant_id: str = "default", bypass_tenant: bool = False) -> List[Dict[str, Any]]:
        if isinstance(tenant_id, bool):
            bypass_tenant = tenant_id
            tenant_id = "default"
        if not tenant_id:
            tenant_id = "default"
        if not bypass_tenant and not tenant_id:
            raise ValueError("tenant_id is required")
        async with memory_repositories._lock:
            res = []
            for a in memory_repositories.remediation_attempts.values():
                if a.get("finding_id") == finding_id:
                    if _check_tenant(a, tenant_id, bypass_tenant, "list_attempts", f"finding:{finding_id}"):
                        res.append(a)
            return res

    async def get_latest_attempt_for_finding(self, finding_id: str, tenant_id: str = "default", bypass_tenant: bool = False) -> Optional[Dict[str, Any]]:
        if isinstance(tenant_id, bool):
            bypass_tenant = tenant_id
            tenant_id = "default"
        if not tenant_id:
            tenant_id = "default"
        if not bypass_tenant and not tenant_id:
            raise ValueError("tenant_id is required")
        async with memory_repositories._lock:
            attempts = []
            for a in memory_repositories.remediation_attempts.values():
                if a.get("finding_id") == finding_id:
                    if _check_tenant(a, tenant_id, bypass_tenant, "get_latest_attempt", f"finding:{finding_id}"):
                        attempts.append(a)
            if not attempts:
                return None
            return sorted(attempts, key=lambda x: x.get("created_at") or datetime.min.replace(tzinfo=timezone.utc), reverse=True)[0]

    async def list_attempts(self, tenant_id: str = "default", limit: int = 50, bypass_tenant: bool = False) -> List[Dict[str, Any]]:
        if isinstance(tenant_id, bool):
            bypass_tenant = tenant_id
            tenant_id = "default"
        elif isinstance(tenant_id, int):
            if isinstance(limit, bool):
                bypass_tenant = limit
                limit = tenant_id
            else:
                limit = tenant_id
            tenant_id = "default"
        if not tenant_id:
            tenant_id = "default"
        if not bypass_tenant and not tenant_id:
            raise ValueError("tenant_id is required")
        async with memory_repositories._lock:
            res = []
            for a in memory_repositories.remediation_attempts.values():
                if _check_tenant(a, tenant_id, bypass_tenant, "list_attempts", "attempts"):
                    res.append(a)
            return sorted(res, key=lambda x: x.get("created_at") or datetime.min.replace(tzinfo=timezone.utc), reverse=True)[:limit]

    async def update_attempt(self, attempt_id: str, updates: Dict[str, Any], tenant_id: str = "default", bypass_tenant: bool = False) -> Optional[Dict[str, Any]]:
        if isinstance(tenant_id, bool):
            bypass_tenant = tenant_id
            tenant_id = "default"
        if not tenant_id:
            tenant_id = "default"
        async with memory_repositories._lock:
            obj = memory_repositories.remediation_attempts.get(attempt_id)
            if not obj:
                return None
            if not _check_tenant(obj, tenant_id, bypass_tenant, "update_attempt", f"remediation_attempt:{attempt_id}"):
                return None
            for k, v in updates.items():
                obj[k] = v
            obj["updated_at"] = datetime.now(timezone.utc)
            return obj


@compatibility_class_decorator
class InMemoryAutonomyDecisionRepository(AutonomyDecisionRepository):
    async def create(self, decision: Dict[str, Any], tenant_id: str = "default") -> Dict[str, Any]:
        if not tenant_id:
            tenant_id = "default"
        async with memory_repositories._lock:
            dec_id = f"dec_{uuid.uuid4().hex[:8]}"
            dec = decision.copy()
            dec["id"] = dec_id
            dec["decision_id"] = dec_id
            dec["tenant_id"] = tenant_id
            dec["created_at"] = datetime.now(timezone.utc)
            dec["updated_at"] = datetime.now(timezone.utc)
            memory_repositories.autonomy_decisions[dec_id] = dec
            return dec

    async def get(self, decision_id: str, tenant_id: str = "default", bypass_tenant: bool = False) -> Optional[Dict[str, Any]]:
        if isinstance(tenant_id, bool):
            bypass_tenant = tenant_id
            tenant_id = "default"
        if not tenant_id:
            tenant_id = "default"
        async with memory_repositories._lock:
            obj = memory_repositories.autonomy_decisions.get(decision_id)
            if not obj:
                return None
            if not _check_tenant(obj, tenant_id, bypass_tenant, "get", f"autonomy_decision:{decision_id}"):
                return None
            return obj

    async def list_by_incident(self, incident_id: str, tenant_id: str = "default", bypass_tenant: bool = False) -> List[Dict[str, Any]]:
        if isinstance(tenant_id, bool):
            bypass_tenant = tenant_id
            tenant_id = "default"
        if not tenant_id:
            tenant_id = "default"
        if not bypass_tenant and not tenant_id:
            raise ValueError("tenant_id is required")
        async with memory_repositories._lock:
            res = []
            for dec in memory_repositories.autonomy_decisions.values():
                if dec.get("incident_id") == incident_id:
                    if _check_tenant(dec, tenant_id, bypass_tenant, "list_decisions", f"incident:{incident_id}"):
                        res.append(dec)
            return sorted(res, key=lambda x: x.get("created_at") or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
