
"""
services/improve/verifier_mesh.py — Phase 28
Orchestrates the execution of all specialized verifiers for a candidate patch.
"""
from typing import List, Dict, Any
from services.improve.models import RepairCandidate, CandidateEvaluation, CandidateScore
from services.improve.benchmark_loader import BenchmarkCase
from services.improve.verifiers.primary_verifiers import BuildVerifier, RegressionVerifier, GovernanceVerifier
from services.improve.verifiers.secondary_verifiers import EconomicVerifier, MeshVerifier, FederationVerifier, OpsVerifier
from services.observability.logging import get_logger

logger = get_logger("repair.verifier_mesh")

class VerifierMesh:
    def __init__(self):
        self.verifiers = [
            BuildVerifier(),
            RegressionVerifier(),
            GovernanceVerifier(),
            EconomicVerifier(),
            MeshVerifier(),
            FederationVerifier(),
            OpsVerifier()
        ]

    async def verify_candidate(self, case: BenchmarkCase, candidate: RepairCandidate) -> CandidateEvaluation:
        """Runs all verifiers and aggregates the scores."""
        logger.info(f"Running Verifier Mesh for candidate: {candidate.id}")
        
        results = {}
        for v in self.verifiers:
            res = await v.verify(case, candidate)
            results[v.name] = res
            logger.debug(f"  Verifier {v.name}: {res.score:.2f} ({res.status})")

        # Map to CandidateScore
        score = CandidateScore(
            syntax_score=results["build"].score,
            regression_score=results["regression"].score,
            policy_score=results["governance"].score,
            risk_score=results["mesh"].score,
            economic_score=results["economic"].score,
            similarity_score=results["federation"].score, # Using federation as a proxy for similarity in this simplified model
            breakdown={v_name: res.score for v_name, res in results.items()},
            justification=f"Mesh complete. Build: {results['build'].status}, Regression: {results['regression'].score:.2f}"
        )

        # Weighted calculation happens in ranker, but we compute a mesh summary here
        total_mesh_score = sum(r.score for r in results.values()) / len(results)
        score.total_score = total_mesh_score

        return CandidateEvaluation(
            candidate_id=candidate.id,
            scores=score,
            is_qualified=all(r.status == "passed" for r in results.values()) and results["build"].score > 0.0
        )
