import hashlib
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from apps.bilgeapi.repositories.interface import PrDraftRepository, ImprovementRepository
from apps.bilgeapi.services.audit import AuditService
from apps.bilgeapi.adapters.github_pr import BaseGitHubPrAdapter

logger = logging.getLogger(__name__)


class PatchRiskAnalyzer:
    def parse_affected_files(self, patch_code: str) -> List[str]:
        affected = []
        if not patch_code:
            return affected
        for line in patch_code.splitlines():
            if line.startswith("+++ b/"):
                file_path = line[6:].strip()
                if file_path not in affected:
                    affected.append(file_path)
        return affected

    def analyze_risk(self, patch_code: str) -> Dict[str, Any]:
        affected_files = self.parse_affected_files(patch_code)
        risk_flags = []
        
        # Risk indicators
        sensitive_patterns = [
            "auth.py",
            "config.py",
            "database.py",
            "migrations/",
            "alembic/",
            "Dockerfile",
            "docker-compose",
            "deploy",
            "k8s",
            "helm"
        ]

        for file_path in affected_files:
            for pattern in sensitive_patterns:
                if pattern in file_path:
                    risk_flags.append(file_path)
                    break

        risk_level = "HIGH" if risk_flags else "LOW"

        return {
            "risk_level": risk_level,
            "risk_flags": risk_flags,
            "affected_files": affected_files
        }


class PrDraftBodyBuilder:
    @staticmethod
    def build_body(
        title: str,
        rationale: str,
        patch_code: str,
        affected_files: List[str],
        risk_level: str,
        risk_flags: List[str],
        confidence_score: float,
        confidence_level: str
    ) -> str:
        affected_files_md = "\n".join(f"- `{f}`" for f in affected_files) if affected_files else "None"
        
        risk_section = f"- Risk Level: **{risk_level}**\n"
        if risk_level == "HIGH":
            risk_section += (
                "\n> [!WARNING]\n"
                "> **High Risk Review Required**: This patch modifies sensitive configuration, authentication, database, or deployment files.\n"
            )
            if risk_flags:
                risk_section += "\nRisky files affected:\n" + "\n".join(f"- `{rf}`" for rf in risk_flags) + "\n"
        else:
            risk_section += "- Side Effects: None expected.\n"

        body = (
            f"### 1. Problem Özeti\n"
            f"Autonomous self-improvement proposal based on query: '{title}'.\n\n"
            f"### 2. Rationale & Evidence Chain\n"
            f"Confidence Score: {confidence_score:.2f} ({confidence_level})\n"
            f"{rationale}\n\n"
            f"### 3. Önerilen Değişiklik\n"
            f"```diff\n{patch_code}```\n\n"
            f"### 4. Etkilenen Dosyalar\n"
            f"{affected_files_md}\n\n"
            f"### 5. Risk Analizi\n"
            f"{risk_section}\n"
            f"### 6. Test Planı\n"
            f"- Run release gate checks (/run-gate).\n"
            f"- Verify all unit and integration tests pass.\n\n"
            f"### 7. Rollback Planı\n"
            f"Discard branch changes or revert the merged PR.\n\n"
            f"### 8. Human Review Checklist\n"
            f"- [ ] Verify security logic and input validation.\n"
            f"- [ ] Check that no credentials/secrets are leaked.\n"
            f"- [ ] Run test suite manually to verify functionality.\n"
        )
        return body


class PrDraftService:
    def __init__(
        self,
        pr_draft_repo: PrDraftRepository,
        proposal_repo: ImprovementRepository,
        github_adapter: BaseGitHubPrAdapter,
        audit_service: AuditService
    ):
        self.pr_draft_repo = pr_draft_repo
        self.proposal_repo = proposal_repo
        self.github_adapter = github_adapter
        self.audit_service = audit_service
        self.risk_analyzer = PatchRiskAnalyzer()

    async def _write_audit_event(self, event_type: str, proposal_id: str, actor_id: str, metadata: Dict[str, Any] = None):
        await self.audit_service.log_event(
            event_type=event_type,
            actor_id=actor_id,
            actor_type="user",
            entity_type="proposal",
            entity_id=proposal_id,
            metadata=metadata or {}
        )

    async def create_draft_pr(self, proposal_id: str, actor_id: str) -> Dict[str, Any]:
        await self._write_audit_event("PR_DRAFT_REQUESTED", proposal_id, actor_id)

        proposal = await self.proposal_repo.get_proposal(proposal_id)
        if not proposal:
            await self._write_audit_event("PR_DRAFT_FAILED", proposal_id, actor_id, {"reason": "Proposal not found"})
            raise ValueError(f"Proposal not found: {proposal_id}")

        # Check approval status
        if proposal.get("approval_status") != "APPROVED":
            await self._write_audit_event("PR_DRAFT_BLOCKED_UNAPPROVED", proposal_id, actor_id)
            raise ValueError("Proposal is not approved. Draft PR cannot be created.")

        # Check gate status
        if proposal.get("gate_status") != "GATE_PASSED":
            await self._write_audit_event("PR_DRAFT_BLOCKED_GATE_FAILED", proposal_id, actor_id)
            raise ValueError("Proposal has not passed release gate simulation. Draft PR cannot be created.")

        # Check confidence level
        risk_analysis = proposal.get("risk_analysis") or {}
        confidence_level = risk_analysis.get("confidence_level", "UNKNOWN")
        confidence_score = risk_analysis.get("confidence_score", 0.0)

        if confidence_level == "LOW":
            await self._write_audit_event("PR_DRAFT_BLOCKED_LOW_CONFIDENCE", proposal_id, actor_id)
            raise ValueError("Low confidence proposals cannot generate PR drafts.")

        patch_code = proposal.get("patch_code", "")

        # Analyze risk
        analysis_result = self.risk_analyzer.analyze_risk(patch_code)
        risk_level = analysis_result["risk_level"]
        risk_flags = analysis_result["risk_flags"]
        affected_files = analysis_result["affected_files"]

        # Build PR body
        body = PrDraftBodyBuilder.build_body(
            title=proposal["title"],
            rationale=proposal["rationale"],
            patch_code=patch_code,
            affected_files=affected_files,
            risk_level=risk_level,
            risk_flags=risk_flags,
            confidence_score=confidence_score,
            confidence_level=confidence_level
        )

        branch_name = f"bilgeapi-patch-{proposal_id}"
        evidence_hash = hashlib.sha256(proposal["rationale"].encode("utf-8")).hexdigest()[:16]

        draft_data = {
            "proposal_id": proposal_id,
            "provider": "github" if hasattr(self.github_adapter, "allow_real") and self.github_adapter.allow_real else "mock",
            "status": "PENDING",
            "github_pr_url": None,
            "branch_name": branch_name,
            "title": f"Draft PR: {proposal['title']}",
            "body": body,
            "evidence_hash": evidence_hash,
            "risk_level": risk_level,
            "risk_flags": risk_flags,
            "created_by": actor_id
        }

        # Create draft PR entry in DB
        db_draft = await self.pr_draft_repo.create_pr_draft(draft_data)

        try:
            # Create draft PR on GitHub
            pr_url = await self.github_adapter.create_draft_pr(
                title=draft_data["title"],
                body=body,
                branch_name=branch_name,
                patch_code=patch_code,
                affected_files=affected_files
            )
            
            # Update draft PR entry status
            updated_draft = await self.pr_draft_repo.update_pr_draft_status(
                draft_id=db_draft["id"],
                status="COMPLETED",
                github_pr_url=pr_url
            )
            
            await self._write_audit_event("PR_DRAFT_CREATED", proposal_id, actor_id, {
                "pr_draft_id": db_draft["id"],
                "github_pr_url": pr_url,
                "risk_level": risk_level
            })

            return updated_draft

        except Exception as e:
            await self.pr_draft_repo.update_pr_draft_status(
                draft_id=db_draft["id"],
                status="FAILED",
                error_message=str(e)
            )
            await self._write_audit_event("PR_DRAFT_FAILED", proposal_id, actor_id, {
                "pr_draft_id": db_draft["id"],
                "error": str(e)
            })
            raise e
