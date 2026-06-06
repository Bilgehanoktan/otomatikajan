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
    ApiKeyRepository
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

memory_repositories = MemoryRepositoriesContainer()


class InMemoryIncidentRepository(IncidentRepository):
    async def create(self, incident: IncidentCreate) -> IncidentResponse:
        async with memory_repositories._lock:
            inc_id = f"inc_{uuid.uuid4().hex[:8]}"
            response = IncidentResponse(
                id=inc_id,
                created_at=datetime.now(timezone.utc),
                **incident.model_dump()
            )
            memory_repositories.incidents[inc_id] = response
            return response

    async def get(self, incident_id: str) -> Optional[IncidentResponse]:
        async with memory_repositories._lock:
            return memory_repositories.incidents.get(incident_id)

    async def list_all(self, project_key: Optional[str] = None) -> List[IncidentResponse]:
        async with memory_repositories._lock:
            all_incidents = list(memory_repositories.incidents.values())
            if project_key:
                return [i for i in all_incidents if i.project_key == project_key]
            return all_incidents


class InMemoryDiagnosticRepository(DiagnosticRepository):
    async def create(self, incident_id: str) -> DiagnosticResult:
        async with memory_repositories._lock:
            diag_id = f"diag_{uuid.uuid4().hex[:8]}"
            result = DiagnosticResult(
                diagnostic_id=diag_id,
                incident_id=incident_id,
                status=DiagnosticStatus.QUEUED,
                created_at=datetime.now(timezone.utc)
            )
            memory_repositories.diagnostics[diag_id] = result
            return result

    async def get(self, diagnostic_id: str) -> Optional[DiagnosticResult]:
        async with memory_repositories._lock:
            return memory_repositories.diagnostics.get(diagnostic_id)

    async def update(self, diagnostic_id: str, status: DiagnosticStatus, **kwargs) -> Optional[DiagnosticResult]:
        async with memory_repositories._lock:
            if diagnostic_id not in memory_repositories.diagnostics:
                return None
            diag = memory_repositories.diagnostics[diagnostic_id]
            
            # Create a copy with updated values
            updated_data = diag.model_dump()
            updated_data["status"] = status
            for k, v in kwargs.items():
                updated_data[k] = v
            
            if status in (DiagnosticStatus.COMPLETED, DiagnosticStatus.FAILED) and not updated_data.get("completed_at"):
                updated_data["completed_at"] = datetime.now(timezone.utc)
                
            updated_diag = DiagnosticResult(**updated_data)
            memory_repositories.diagnostics[diagnostic_id] = updated_diag
            return updated_diag

    async def list_all(self) -> List[DiagnosticResult]:
        async with memory_repositories._lock:
            return list(memory_repositories.diagnostics.values())


class InMemoryFindingRepository(FindingRepository):
    async def create(self, diagnostic_id: str, finding_data: Dict[str, Any]) -> Dict[str, Any]:
        async with memory_repositories._lock:
            if diagnostic_id not in memory_repositories.findings:
                memory_repositories.findings[diagnostic_id] = []
            
            f_id = f"find_{uuid.uuid4().hex[:8]}"
            finding = {"id": f_id, "diagnostic_id": diagnostic_id, **finding_data}
            memory_repositories.findings[diagnostic_id].append(finding)
            return finding

    async def list_by_diagnostic(self, diagnostic_id: str) -> List[Dict[str, Any]]:
        async with memory_repositories._lock:
            return memory_repositories.findings.get(diagnostic_id, [])


class InMemoryRecommendationRepository(RecommendationRepository):
    async def create(self, diagnostic_id: str, recommendation_data: Dict[str, Any]) -> Dict[str, Any]:
        async with memory_repositories._lock:
            if diagnostic_id not in memory_repositories.recommendations:
                memory_repositories.recommendations[diagnostic_id] = []
            
            r_id = f"rec_{uuid.uuid4().hex[:8]}"
            recommendation = {"id": r_id, "diagnostic_id": diagnostic_id, **recommendation_data}
            memory_repositories.recommendations[diagnostic_id].append(recommendation)
            return recommendation

    async def list_by_diagnostic(self, diagnostic_id: str) -> List[Dict[str, Any]]:
        async with memory_repositories._lock:
            return memory_repositories.recommendations.get(diagnostic_id, [])


class InMemoryRepairRequestRepository(RepairRequestRepository):
    async def create(self, diagnostic_id: str, request: RepairRequestCreate) -> RepairRequestResponse:
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
            memory_repositories.repair_requests[rep_id] = response
            return response

    async def get(self, repair_request_id: str) -> Optional[RepairRequestResponse]:
        async with memory_repositories._lock:
            return memory_repositories.repair_requests.get(repair_request_id)

    async def update(self, repair_request_id: str, approval_status: ApprovalStatus, dispatch_status: DispatchStatus, **kwargs) -> Optional[RepairRequestResponse]:
        async with memory_repositories._lock:
            if repair_request_id not in memory_repositories.repair_requests:
                return None
            rep = memory_repositories.repair_requests[repair_request_id]
            updated_data = rep.model_dump()
            updated_data["approval_status"] = approval_status
            updated_data["dispatch_status"] = dispatch_status
            updated_data["updated_at"] = datetime.now(timezone.utc)
            for k, v in kwargs.items():
                updated_data[k] = v
            
            updated_rep = RepairRequestResponse(**updated_data)
            memory_repositories.repair_requests[repair_request_id] = updated_rep
            return updated_rep

    async def list_all(self) -> List[RepairRequestResponse]:
        async with memory_repositories._lock:
            return list(memory_repositories.repair_requests.values())


class InMemoryAuditRepository(AuditRepository):
    async def write(self, event: AuditEvent) -> None:
        async with memory_repositories._lock:
            memory_repositories.audit_events.append(event)

    async def list_recent(self, limit: int = 100) -> List[AuditEvent]:
        async with memory_repositories._lock:
            # Return last N events ordered by created_at descending
            events = sorted(memory_repositories.audit_events, key=lambda e: e.created_at, reverse=True)
            return events[:limit]


class InMemoryWebhookDeliveryRepository(WebhookDeliveryRepository):
    async def log_delivery(self, delivery_data: Dict[str, Any]) -> None:
        async with memory_repositories._lock:
            delivery_data = delivery_data.copy()
            if "id" not in delivery_data:
                delivery_data["id"] = f"web_{uuid.uuid4().hex[:8]}"
            if "created_at" not in delivery_data:
                delivery_data["created_at"] = datetime.now(timezone.utc)
            memory_repositories.webhook_deliveries.append(delivery_data)

    async def create_delivery(self, delivery_data: Dict[str, Any]) -> Dict[str, Any]:
        async with memory_repositories._lock:
            delivery_data = delivery_data.copy()
            del_id = f"web_{uuid.uuid4().hex[:8]}"
            delivery_data["id"] = del_id
            delivery_data["created_at"] = datetime.now(timezone.utc)
            memory_repositories.webhook_deliveries.append(delivery_data)
            return delivery_data

    async def update_delivery(self, delivery_id: str, delivery_status: str, status_code: Optional[float], error_message: Optional[str], attempt_count: float) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            for item in memory_repositories.webhook_deliveries:
                if item.get("id") == delivery_id:
                    item["delivery_status"] = delivery_status
                    item["status_code"] = status_code
                    item["error_message"] = error_message
                    item["attempt_count"] = attempt_count
                    return item
            return None

    async def get_delivery(self, delivery_id: str) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            for item in memory_repositories.webhook_deliveries:
                if item.get("id") == delivery_id:
                    return item
            return None

    async def list_deliveries(self) -> List[Dict[str, Any]]:
        async with memory_repositories._lock:
            # Sort with fallback if created_at is missing (unlikely)
            return sorted(memory_repositories.webhook_deliveries, key=lambda d: d.get("created_at") or datetime.min.replace(tzinfo=timezone.utc), reverse=True)


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
            sorted_checks = sorted(
                memory_repositories.release_checks,
                key=lambda d: d.get("created_at") or datetime.min.replace(tzinfo=timezone.utc),
                reverse=True
            )
            return sorted_checks[0]

    async def list_checks(self, limit: int = 20) -> List[Dict[str, Any]]:
        async with memory_repositories._lock:
            sorted_checks = sorted(
                memory_repositories.release_checks,
                key=lambda d: d.get("created_at") or datetime.min.replace(tzinfo=timezone.utc),
                reverse=True
            )
            return sorted_checks[:limit]


class InMemoryApiKeyRepository(ApiKeyRepository):
    async def create(self, key_data: Dict[str, Any]) -> Dict[str, Any]:
        async with memory_repositories._lock:
            key_data = key_data.copy()
            if "id" not in key_data:
                key_data["id"] = f"key_{uuid.uuid4().hex[:8]}"
            if "created_at" not in key_data:
                key_data["created_at"] = datetime.now(timezone.utc)
            if "is_active" not in key_data:
                key_data["is_active"] = True
            
            memory_repositories.api_keys[key_data["id"]] = key_data
            return key_data

    async def get(self, key_id: str) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            return memory_repositories.api_keys.get(key_id)

    async def get_by_hash(self, key_hash: str) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            for item in memory_repositories.api_keys.values():
                if item.get("key_hash") == key_hash:
                    return item
            return None

    async def list_all(self) -> List[Dict[str, Any]]:
        async with memory_repositories._lock:
            # Sort by created_at desc
            return sorted(
                memory_repositories.api_keys.values(),
                key=lambda d: d.get("created_at") or datetime.min.replace(tzinfo=timezone.utc),
                reverse=True
            )

    async def revoke(self, key_id: str, revoked_by: str, reason: str) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            item = memory_repositories.api_keys.get(key_id)
            if not item:
                return None
            item["is_active"] = False
            item["revoked_by"] = revoked_by
            item["revoke_reason"] = reason
            item["revoked_at"] = datetime.now(timezone.utc)
            return item

    async def update_last_used(self, key_id: str, last_used: datetime) -> None:
        async with memory_repositories._lock:
            item = memory_repositories.api_keys.get(key_id)
            if item:
                item["last_used_at"] = last_used

    async def update_quota(self, key_id: str, quota_daily: Optional[int], quota_monthly: Optional[int]) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            item = memory_repositories.api_keys.get(key_id)
            if not item:
                return None
            item["quota_daily"] = quota_daily
            item["quota_monthly"] = quota_monthly
            return item


