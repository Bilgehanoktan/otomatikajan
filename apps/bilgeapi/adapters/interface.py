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
