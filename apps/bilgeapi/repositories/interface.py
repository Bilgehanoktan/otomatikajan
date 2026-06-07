from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any
from apps.bilgeapi.schemas.incident import IncidentCreate, IncidentResponse
from apps.bilgeapi.schemas.diagnostic import DiagnosticResult, DiagnosticStatus
from apps.bilgeapi.schemas.repair import RepairRequestCreate, RepairRequestResponse, ApprovalStatus, DispatchStatus
from apps.bilgeapi.schemas.audit import AuditEvent

class IncidentRepository(ABC):
    @abstractmethod
    async def create(self, incident: IncidentCreate) -> IncidentResponse:
        pass

    @abstractmethod
    async def get(self, incident_id: str) -> Optional[IncidentResponse]:
        pass

    @abstractmethod
    async def list_all(self, project_key: Optional[str] = None) -> List[IncidentResponse]:
        pass


class DiagnosticRepository(ABC):
    @abstractmethod
    async def create(self, incident_id: str) -> DiagnosticResult:
        pass

    @abstractmethod
    async def get(self, diagnostic_id: str) -> Optional[DiagnosticResult]:
        pass

    @abstractmethod
    async def update(self, diagnostic_id: str, status: DiagnosticStatus, **kwargs) -> Optional[DiagnosticResult]:
        pass

    @abstractmethod
    async def list_all(self) -> List[DiagnosticResult]:
        pass


class FindingRepository(ABC):
    @abstractmethod
    async def create(self, diagnostic_id: str, finding_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def list_by_diagnostic(self, diagnostic_id: str) -> List[Dict[str, Any]]:
        pass


class RecommendationRepository(ABC):
    @abstractmethod
    async def create(self, diagnostic_id: str, recommendation_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def list_by_diagnostic(self, diagnostic_id: str) -> List[Dict[str, Any]]:
        pass


class RepairRequestRepository(ABC):
    @abstractmethod
    async def create(self, diagnostic_id: str, request: RepairRequestCreate) -> RepairRequestResponse:
        pass

    @abstractmethod
    async def get(self, repair_request_id: str) -> Optional[RepairRequestResponse]:
        pass

    @abstractmethod
    async def update(self, repair_request_id: str, approval_status: ApprovalStatus, dispatch_status: DispatchStatus, **kwargs) -> Optional[RepairRequestResponse]:
        pass

    @abstractmethod
    async def list_all(self) -> List[RepairRequestResponse]:
        pass


class AuditRepository(ABC):
    @abstractmethod
    async def write(self, event: AuditEvent) -> None:
        pass

    @abstractmethod
    async def list_recent(self, limit: int = 100) -> List[AuditEvent]:
        pass


class WebhookDeliveryRepository(ABC):
    @abstractmethod
    async def log_delivery(self, delivery_data: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    async def create_delivery(self, delivery_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def update_delivery(self, delivery_id: str, delivery_status: str, status_code: Optional[float], error_message: Optional[str], attempt_count: float) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def get_delivery(self, delivery_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def list_deliveries(self) -> List[Dict[str, Any]]:
        pass


class ReleaseCheckRepository(ABC):
    @abstractmethod
    async def create_check(self, check_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_latest_check(self) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def list_checks(self, limit: int = 20) -> List[Dict[str, Any]]:
        pass


class ApiKeyRepository(ABC):
    @abstractmethod
    async def create(self, key_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get(self, key_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def get_by_hash(self, key_hash: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def list_all(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def revoke(self, key_id: str, revoked_by: str, reason: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def update_last_used(self, key_id: str, last_used: datetime) -> None:
        pass

    @abstractmethod
    async def update_quota(self, key_id: str, quota_daily: Optional[int], quota_monthly: Optional[int]) -> Optional[Dict[str, Any]]:
        pass


class ResearchRepository(ABC):
    @abstractmethod
    async def create_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def update_request_status(self, request_id: str, status: str, error_message: Optional[str] = None) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def create_evidence(self, evidence_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def list_evidences(self, research_id: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def get_tenant_daily_research_count(self, tenant_id: str, day: datetime) -> int:
        pass


class ImprovementRepository(ABC):
    @abstractmethod
    async def create_proposal(self, proposal_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_proposal(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def update_proposal_gate(self, proposal_id: str, gate_status: str, gate_score: Optional[float] = None, risk_analysis: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def approve_proposal(self, proposal_id: str, approved_by: str, approved_at: datetime) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def list_proposals(self) -> List[Dict[str, Any]]:
        pass


class PrDraftRepository(ABC):
    @abstractmethod
    async def create_pr_draft(self, draft_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_pr_draft(self, draft_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def list_pr_drafts_by_proposal(self, proposal_id: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def update_pr_draft_status(self, draft_id: str, status: str, github_pr_url: Optional[str] = None, error_message: Optional[str] = None) -> Optional[Dict[str, Any]]:
        pass


class PrVerificationRepository(ABC):
    @abstractmethod
    async def create_verification(self, verification_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_verification_by_pr_draft(self, pr_draft_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def list_verifications_by_proposal(self, proposal_id: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def get_verification_by_revision(self, revision_id: str) -> Optional[Dict[str, Any]]:
        pass


class PrReviewFeedbackRepository(ABC):
    @abstractmethod
    async def create_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_feedback(self, feedback_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def list_feedback_by_pr_draft(self, pr_draft_id: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def update_feedback_status(self, feedback_id: str, status: str) -> Optional[Dict[str, Any]]:
        pass


class PatchRevisionRepository(ABC):
    @abstractmethod
    async def create_revision(self, revision_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_revision(self, revision_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def get_latest_revision_number(self, pr_draft_id: str) -> int:
        pass

    @abstractmethod
    async def list_revisions_by_pr_draft(self, pr_draft_id: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def update_verification_status(self, revision_id: str, status: str) -> Optional[Dict[str, Any]]:
        pass



