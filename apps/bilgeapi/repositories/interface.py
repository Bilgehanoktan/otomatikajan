from abc import ABC, abstractmethod
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

