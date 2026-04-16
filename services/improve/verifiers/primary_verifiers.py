
from services.improve.verifiers.base import BaseVerifier, VerifierResult
from services.improve.models import RepairCandidate
from services.improve.benchmark_loader import BenchmarkCase

class BuildVerifier(BaseVerifier):
    @property
    def name(self) -> str: return "build"

    async def verify(self, case: BenchmarkCase, candidate: RepairCandidate) -> VerifierResult:
        # Simulate import/syntax/lint check
        if "syntax error" in candidate.content.lower():
            return VerifierResult(0.0, {"error": "Syntax error detected"}, "failed")
        return VerifierResult(1.0, {"build": "successful", "lint": "clean"})

class RegressionVerifier(BaseVerifier):
    @property
    def name(self) -> str: return "regression"

    async def verify(self, case: BenchmarkCase, candidate: RepairCandidate) -> VerifierResult:
        # Simulate unit and integration tests
        score = 0.9
        if candidate.strategy == "radical": score = 0.5
        return VerifierResult(score, {"tests_passed": 45, "tests_failed": 0})

class GovernanceVerifier(BaseVerifier):
    @property
    def name(self) -> str: return "governance"

    async def verify(self, case: BenchmarkCase, candidate: RepairCandidate) -> VerifierResult:
        # Simulate RBAC and policy drift check
        return VerifierResult(1.0, {"rbac_impact": "none", "policy_drift": "none"})
