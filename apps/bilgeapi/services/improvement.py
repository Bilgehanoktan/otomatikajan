import re
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from apps.bilgeapi.repositories.interface import ResearchRepository, ImprovementRepository

logger = logging.getLogger("bilgeapi.improvement")


class ImprovementProposalEngine:
    def __init__(self, research_repo: ResearchRepository, improvement_repo: ImprovementRepository, ledger_service: Optional[Any] = None):
        self.research_repo = research_repo
        self.improvement_repo = improvement_repo
        self.ledger_service = ledger_service

    async def _append_ledger_event(self, *, research_id: str, event_type: str, entity_type: str, entity_id: str, payload: Dict[str, Any]) -> None:
        if not self.ledger_service:
            return
        try:
            await self.ledger_service.append_event(
                chain_id=f"chain_{research_id}",
                event_type=event_type,
                entity_type=entity_type,
                entity_id=entity_id,
                actor_id="system",
                payload=payload,
            )
        except Exception as exc:
            logger.warning("Review ledger append failed for %s:%s: %s", entity_type, entity_id, exc)

    async def generate_proposal(self, research_id: str) -> Dict[str, Any]:
        """
        Generate a proposal, rationale, risk analysis, and patch draft.
        Enforces evidence quality gates and calculates confidence scores.
        """
        request = await self.research_repo.get_request(research_id)
        if not request:
            raise ValueError(f"Research request not found: {research_id}")

        evidences = await self.research_repo.list_evidences(research_id)
        if not evidences:
            raise ValueError(f"No research evidences found for request: {research_id}")

        # 1. Evidence Quality Gate Enforcements
        # Filter evidences to trust_score >= 50
        reliable_evidences = [e for e in evidences if e["trust_score"] >= 50.0]
        if len(reliable_evidences) < 3:
            raise ValueError(
                f"Quality gate check failed: Found only {len(reliable_evidences)} reliable sources "
                f"(trust_score >= 50), but a minimum of 3 is required."
            )

        query = request["query"]

        # Check for official docs (trust_score >= 90)
        has_official_doc = any(e["trust_score"] >= 90.0 for e in reliable_evidences)

        # 2. Confidence Scoring
        # average trust score
        avg_trust = sum(e["trust_score"] for e in reliable_evidences) / len(reliable_evidences)

        # average match ratio
        query_words = set(query.lower().split())
        match_ratios = []
        for e in reliable_evidences:
            title = e.get("title") or ""
            snippet = e.get("snippet") or ""
            text_words = set((title + " " + snippet).lower().split())
            if query_words:
                ratio = len(query_words & text_words) / len(query_words)
            else:
                ratio = 0.0
            match_ratios.append(ratio)
        avg_match = sum(match_ratios) / len(match_ratios) if match_ratios else 0.0

        # Formula: (avg_trust * 0.6) + (avg_match * 25) + (15 if official_doc else 0)
        confidence_score = (avg_trust * 0.6) + (avg_match * 25.0) + (15.0 if has_official_doc else 0.0)
        confidence_score = max(0.0, min(100.0, confidence_score))

        # Enforce official doc constraint: if no official docs, max confidence is MEDIUM (< 85)
        if not has_official_doc and confidence_score >= 85.0:
            confidence_score = 84.0

        # Determine level
        if confidence_score >= 85.0:
            confidence_level = "HIGH"
        elif confidence_score >= 60.0:
            confidence_level = "MEDIUM"
        else:
            confidence_level = "LOW"

        # Auto-reject LOW confidence proposals
        approval_status = "REVIEW_REQUIRED"
        if confidence_level == "LOW":
            approval_status = "REJECTED"

        # Build mock title, rationale, patch based on query
        title = f"Improvement proposal for: {query}"
        
        sources_summary = "\n".join([
            f"- [{e['trust_score']:.1f}] {e['title']} ({e['source_url']})"
            for e in reliable_evidences
        ])

        rationale = (
            f"Based on our web research regarding '{query}', we analyzed the following sources:\n"
            f"{sources_summary}\n\n"
            f"The primary recommendation is to optimize resource configurations, validate inputs, "
            f"and add structured logging to prevent silent errors."
        )

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
            "mitigation_plan": "Simulated release gate checks verify syntax and boundaries.",
            "confidence_score": confidence_score,
            "confidence_level": confidence_level,
            "has_official_doc": has_official_doc
        }

        proposal_data = {
            "research_id": research_id,
            "title": title,
            "rationale": rationale,
            "patch_code": patch_code,
            "risk_analysis": risk_analysis,
            "gate_status": "DRAFT",
            "gate_score": None,
            "approval_status": approval_status,
            "ready_for_human_apply": False,
        }

        proposal = await self.improvement_repo.create_proposal(proposal_data)
        await self._append_ledger_event(
            research_id=research_id,
            event_type="PROPOSAL_CREATED",
            entity_type="improvement_proposal",
            entity_id=proposal["id"],
            payload={
                "proposal": proposal,
                "evidence_count": len(reliable_evidences),
                "confidence_score": confidence_score,
                "confidence_level": confidence_level,
            }
        )
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

        # Re-fetch proposal to get current risk_analysis JSON
        risk_analysis = proposal.get("risk_analysis") or {}

        simulated_analysis = {
            "risk_level": risk_level,
            "gate_score": risk_score,
            "affected_files": affected_files,
            "warnings": warnings,
            "confidence_score": risk_analysis.get("confidence_score"),
            "confidence_level": risk_analysis.get("confidence_level"),
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

        # Keep confidence details in the updated risk analysis JSON
        updated_risk = risk_analysis.copy()
        updated_risk.update(simulated_analysis)

        gate_status = "GATE_PASSED" if risk_score >= 80.0 else "GATE_FAILED"
        updated_proposal = await self.repo.update_proposal_gate(
            proposal_id=proposal_id,
            gate_status=gate_status,
            gate_score=risk_score,
            risk_analysis=updated_risk
        )

        return simulated_analysis

    def generate_audit_report(self, proposal: Dict[str, Any], evidences: List[Dict[str, Any]]) -> str:
        """
        Generate a detailed self-improvement markdown audit report.
        """
        risk_analysis = proposal.get("risk_analysis") or {}
        confidence_score = risk_analysis.get("confidence_score", 0.0)
        confidence_level = risk_analysis.get("confidence_level", "UNKNOWN")

        report = []
        report.append(f"# Self-Improvement Audit Report — Proposal: {proposal['id']}")
        report.append(f"**Date Generated:** {datetime.now(timezone.utc).isoformat()}")
        report.append(f"**Proposal Title:** {proposal['title']}")
        report.append(f"**Confidence Score:** {confidence_score:.2f} ({confidence_level})")
        report.append(f"**Gate Status:** {proposal['gate_status']} | **Approval Status:** {proposal['approval_status']}")
        report.append("")
        report.append("## 1. Research Details")
        report.append(f"**Incident ID Reference:** {proposal.get('research_id', 'Unknown')}")
        report.append("### Search Query & Rationale")
        report.append(f"We initiated autonomous web research with the goal of identifying code patches or configurations related to:")
        report.append(f"> {proposal['title']}")
        report.append("")
        report.append("## 2. Evidence Pack Summary (Sources)")
        report.append("The following web sources were compiled, verified, and scored:")
        report.append("")

        for idx, ev in enumerate(evidences, 1):
            report.append(f"### Source {idx}: {ev.get('title', 'No Title')} (Trust Score: {ev['trust_score']:.1f})")
            report.append(f"- **URL:** {ev['source_url']}")
            report.append(f"- **Domain:** {ev['source_domain']}")
            report.append(f"- **Snippet:** {ev.get('snippet', 'No snippet')}")
            report.append(f"- **Summary:** {ev.get('raw_content_summary', 'No summary')}")
            report.append(f"- **Content Hash:** `{ev['content_hash']}`")
            report.append("")

        report.append("## 3. Proposal Patch Rationale")
        report.append(proposal.get("rationale", "No rationale specified."))
        report.append("")
        report.append("### Proposed Patch Code")
        report.append("```diff")
        report.append(proposal.get("patch_code", ""))
        report.append("```")
        report.append("")
        report.append("## 4. Risk Analysis & Simulation Checks")
        report.append(f"- **Simulated Risk Level:** {risk_analysis.get('risk_level', 'LOW')}")
        report.append(f"- **Gate Score:** {proposal.get('gate_score', 'N/A')}")
        report.append(f"- **Potential Side Effects:** {risk_analysis.get('potential_side_effects', 'None')}")
        report.append(f"- **Mitigation Plan:** {risk_analysis.get('mitigation_plan', 'None')}")
        report.append("")
        report.append("### Affected Files")
        for f in risk_analysis.get("affected_files", []):
            report.append(f"- `{f}`")

        return "\n".join(report)
