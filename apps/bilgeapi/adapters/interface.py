from abc import ABC, abstractmethod
from apps.bilgeapi.schemas.incident import IncidentResponse

class DiagnosticAdapter(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    async def run_diagnostic(self, incident: IncidentResponse) -> dict:
        """
        Runs diagnostic analysis on the incident.
        Returns a dict containing:
          - summary: str
          - root_cause_hypothesis: str
          - confidence: float
          - risk_score: float
          - findings: list of dicts
          - recommendations: list of dicts
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        pass


class ExternalAdapter(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def enabled(self) -> bool:
        pass

    @property
    @abstractmethod
    def configured(self) -> bool:
        pass

    @abstractmethod
    async def health_check(self) -> str:
        """
        Returns the health status of the adapter:
        - "healthy": Configured, enabled, and backend resolves/accessible.
        - "unhealthy": Configured and enabled, but backend checks fail.
        - "disabled": Disabled in configuration.
        - "not_configured": Enabled but missing required settings.
        """
        pass

    @abstractmethod
    async def dispatch(self, repair_request_id: str, payload: dict, dry_run: bool = False) -> dict:
        """
        Dispatches the approved repair request.
        Returns a dict containing:
          - status: str ("SENT", "FAILED")
          - external_reference: Optional[str] (e.g. "github:owner/repo#42", "jira:OPS-123")
          - error_message: Optional[str]
          - raw_response: Optional[dict]
        """
        pass
