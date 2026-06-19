
from abc import ABC, abstractmethod
from typing import Dict, Any
from services.improve.models import RepairCandidate
from services.improve.benchmark_loader import BenchmarkCase

class VerifierResult:
    def __init__(self, score: float, details: Dict[str, Any], status: str = "passed"):
        self.score = score
        self.details = details
        self.status = status

class BaseVerifier(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    async def verify(self, case: BenchmarkCase, candidate: RepairCandidate) -> VerifierResult:
        pass
