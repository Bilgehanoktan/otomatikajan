import re
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from apps.bilgeapi.repositories.interface import ResearchRepository, ImprovementRepository

logger = logging.getLogger("bilgeapi.improvement")


class ImprovementProposalEngine:
    def __init__(self, research_repo: ResearchRepository, improvement_repo: ImprovementRepository):
        self.research_repo = research_repo
        self.improvement_repo = improvement_repo

    async def generate_proposal(self, research_id: str) -> Dict[str, Any]:
        """
        Generate a proposal, rationale, risk analysis, and patch draft using LLM logic (mocked).
        """
        request = await self.research_repo.get_request(research_id)
        if not request:
            raise ValueError(f"Research request not found: {research_id}")

        evidences = await self.research_repo.list_evidences(research_id)
        if not evidences:
            raise ValueError(f"No research evidences found for request: {research_id}")

        query = request["query"]

        # Build mock title, rationale, patch based on query
        title = f"Improvement proposal for: {query}"
        
        # Build list of sources for rationale
        sources_summary = "\n".join([
            f"- [{e['trust_score']:.1f}] {e['title']} ({e['source_url']})"
            for e in evidences
        ])

        rationale = (
            f"Based on our web research regarding '{query}', we analyzed the following sources:\n"
            f"{sources_summary}\n\n"
            f"The primary recommendation is to optimize resource configurations, validate inputs, "
            f"and add structured logging to prevent silent errors."
        )

        # Generate a simulated git patch
        patch_code = (
            "diff --git a/apps/bilgeapi/main.py b/apps/bilgeapi/main.py\n"
            "index a1b2c3d..e4f5g6h 100644\n"
            "--- a/apps/bilgeapi/main.py\n"
            "+++ b/apps/bilgeapi/main.py\n"
            "@@ -50,3 +50,7 @@\n"
            " def health_check():\n"
            "     return {'status': 'healthy'}\n"
            "+\n"
            "+# Added via autonomous self-improvement proposal\n"
            "+def self_improve_status():\n"
            "+    return {'self_improve_loop': 'active'}\n"
        )

        risk_analysis = {
            "risk_level": "LOW",
            "impacted_files": ["apps/bilgeapi/main.py"],
            "potential_side_effects": "None expected, adding standard endpoint.",
            "mitigation_plan": "Simulated release gate checks verify syntax and boundaries."
        }

        proposal_data = {
            "research_id": research_id,
            "title": title,
            "rationale": rationale,
            "patch_code": patch_code,
            "risk_analysis": risk_analysis,
            "gate_status": "DRAFT",
            "gate_score": None,
            "approval_status": "REVIEW_REQUIRED",
            "ready_for_human_apply": False,
        }

        proposal = await self.improvement_repo.create_proposal(proposal_data)
        return proposal


class ReleaseGateSimulator:
    def __init__(self, repo: ImprovementRepository):
        self.repo = repo

    def parse_affected_files(self, patch_code: str) -> List[str]:
        """Parse git patch content to extract affected files."""
        affected = []
        for line in patch_code.splitlines():
            if line.startswith("+++ b/"):
                file_path = line[6:]
                if file_path not in affected:
                    affected.append(file_path)
        return affected

    async def run_simulation(self, proposal_id: str) -> Dict[str, Any]:
        """
        Simulate release gate impact checks, test plan generation, and risk analysis without executing code.
        """
        proposal = await self.repo.get_proposal(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal not found: {proposal_id}")

        await self.repo.update_proposal_gate(proposal_id, "GATE_RUNNING")

        patch_code = proposal.get("patch_code", "")
        affected_files = self.parse_affected_files(patch_code)

        # Basic risk analysis simulation
        risk_level = "LOW"
        risk_score = 98.0
        warnings = []

        if not patch_code:
            risk_level = "HIGH"
            risk_score = 0.0
            warnings.append("Patch code is empty.")
        elif "eval(" in patch_code or "exec(" in patch_code:
            risk_level = "HIGH"
            risk_score = 30.0
            warnings.append("Unsafe dynamic execution functions (eval/exec) detected.")
        elif len(affected_files) > 3:
            risk_level = "MEDIUM"
            risk_score = 85.0
            warnings.append("Patch modifies multiple components, which may increase regression risk.")

        simulated_analysis = {
            "risk_level": risk_level,
            "gate_score": risk_score,
            "affected_files": affected_files,
            "warnings": warnings,
            "simulated_test_runs": [
                {
                    "test_suite": "unit_tests",
                    "status": "PASSED",
                    "assertions_checked": 42
                },
                {
                    "test_suite": "regression_tests",
                    "status": "PASSED",
                    "assertions_checked": 128
                }
            ],
            "release_readiness_audit": {
                "score": risk_score,
                "status": "PASSED" if risk_score >= 80.0 else "FAILED",
                "gate_passed": risk_score >= 80.0
            }
        }

        gate_status = "GATE_PASSED" if risk_score >= 80.0 else "GATE_FAILED"
        updated_proposal = await self.repo.update_proposal_gate(
            proposal_id=proposal_id,
            gate_status=gate_status,
            gate_score=risk_score,
            risk_analysis=simulated_analysis
        )

        return simulated_analysis
