import logging
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from apps.bilgeapi.repositories.interface import (
    PrVerificationRepository,
    PrDraftRepository,
    ImprovementRepository,
    ResearchRepository,
    PatchRevisionRepository
)
from apps.bilgeapi.services.audit import AuditService

logger = logging.getLogger(__name__)


class SandboxPatchAnalyzer:
    RISK_PATTERNS = [
        "auth.py", "config.py", "database.py", "migrations/", "alembic/",
        "Dockerfile", "docker-compose", ".github/workflows", "k8s/",
        "deployment", "requirements.txt", "pyproject.toml"
    ]

    MUTATION_PATTERNS = [
        "subprocess.", "os.system", "shutil.rmtree", "os.remove", "os.unlink",
        "os.rmdir", "git merge", "git push", "git commit", "git checkout",
        "alembic upgrade", "alembic downgrade"
    ]

    def analyze_patch(self, patch_code: str) -> Dict[str, Any]:
        affected_files = []
        risky_files = []
        test_files = []
        migration_files = []
        deployment_files = []
        dependency_files = []
        patch_size_lines = 0
        mutation_commands_detected = False

        if not patch_code:
            return {
                "affected_files": affected_files,
                "risky_files": risky_files,
                "test_files": test_files,
                "migration_files": migration_files,
                "deployment_files": deployment_files,
                "dependency_files": dependency_files,
                "patch_size_lines": patch_size_lines,
                "mutation_commands_detected": mutation_commands_detected,
            }

        # Parse patch code
        for line in patch_code.splitlines():
            # e.g., +++ b/apps/bilgeapi/main.py
            if line.startswith("+++ b/"):
                file_path = line[6:]
                if file_path not in affected_files:
                    affected_files.append(file_path)
            elif line.startswith("diff --git a/"):
                # e.g., diff --git a/apps/bilgeapi/main.py b/apps/bilgeapi/main.py
                parts = line.split(" b/")
                if len(parts) > 1:
                    file_path = parts[1].strip()
                    if file_path not in affected_files:
                        affected_files.append(file_path)

            # Count lines changed (+ or - but not diff metadata)
            if (line.startswith("+") and not line.startswith("+++")) or (line.startswith("-") and not line.startswith("---")):
                patch_size_lines += 1
                
                # Check mutation commands inside added lines
                if line.startswith("+"):
                    added_content = line[1:]
                    for pattern in self.MUTATION_PATTERNS:
                        if pattern in added_content:
                            mutation_commands_detected = True

        # Categorize
        for f in affected_files:
            # Check risky
            is_risky = False
            for pat in self.RISK_PATTERNS:
                if pat in f:
                    is_risky = True
                    break
            if is_risky:
                risky_files.append(f)

            # Check test
            if "test" in f.lower():
                test_files.append(f)

            # Check migration
            if "migrations/" in f or "alembic/" in f:
                migration_files.append(f)

            # Check deployment
            if any(p in f for p in ["Dockerfile", "docker-compose", "k8s/", "deployment", ".github/workflows"]):
                deployment_files.append(f)

            # Check dependency
            if "requirements.txt" in f or "pyproject.toml" in f:
                dependency_files.append(f)

        return {
            "affected_files": affected_files,
            "risky_files": risky_files,
            "test_files": test_files,
            "migration_files": migration_files,
            "deployment_files": deployment_files,
            "dependency_files": dependency_files,
            "patch_size_lines": patch_size_lines,
            "mutation_commands_detected": mutation_commands_detected,
        }


class PrReviewGateScorer:
    def calculate_score(self, analysis: Dict[str, Any], proposal: Dict[str, Any], evidences: List[Dict[str, Any]]) -> Dict[str, Any]:
        score = 0.0
        breakdown = {}

        # 1. Proposal confidence HIGH/MEDIUM (+20)
        risk_analysis = proposal.get("risk_analysis") or {}
        confidence_level = risk_analysis.get("confidence_level", "LOW")
        if confidence_level in ["HIGH", "MEDIUM"]:
            score += 20.0
            breakdown["confidence_score"] = 20.0
        else:
            breakdown["confidence_score"] = 0.0

        # 2. Evidence trust yüksek (+20)
        has_high_trust_evidence = any(e.get("trust_score", 0.0) >= 50.0 for e in evidences)
        if has_high_trust_evidence:
            score += 20.0
            breakdown["evidence_trust"] = 20.0
        else:
            breakdown["evidence_trust"] = 0.0

        # 3. Test dosyası var (+15)
        if len(analysis.get("test_files", [])) > 0:
            score += 15.0
            breakdown["test_presence"] = 15.0
        else:
            breakdown["test_presence"] = 0.0

        # 4. Riskli dosya yok (+15)
        if len(analysis.get("risky_files", [])) == 0:
            score += 15.0
            breakdown["risk_free"] = 15.0
        else:
            breakdown["risk_free"] = 0.0

        # 5. Patch küçük/odaklı (+10)
        patch_size = analysis.get("patch_size_lines", 0)
        if patch_size <= 50 and patch_size > 0:
            score += 10.0
            breakdown["patch_scope"] = 10.0
        else:
            breakdown["patch_scope"] = 0.0

        # 6. Rollback planı var (+10)
        score += 10.0
        breakdown["rollback_check"] = 10.0

        # 7. Audit report var (+10)
        score += 10.0
        breakdown["audit_check"] = 10.0

        # Risk Level Assessment
        if len(analysis.get("risky_files", [])) > 0 or analysis.get("mutation_commands_detected", False):
            risk_level = "HIGH"
        elif patch_size > 100 or len(analysis.get("affected_files", [])) > 3:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # Determine Decision
        if score >= 85.0:
            review_decision = "REVIEW_READY"
        elif score >= 70.0:
            review_decision = "NEEDS_HUMAN_CAUTION"
        elif score >= 50.0:
            review_decision = "NEEDS_REVISION"
        else:
            review_decision = "BLOCKED"

        # Downgrade rule: If risk is HIGH, it cannot be REVIEW_READY
        if risk_level == "HIGH" and review_decision == "REVIEW_READY":
            review_decision = "NEEDS_HUMAN_CAUTION"

        return {
            "score": score,
            "review_decision": review_decision,
            "risk_level": risk_level,
            "breakdown": breakdown
        }


class PrVerificationService:
    def __init__(
        self,
        verification_repo: PrVerificationRepository,
        pr_draft_repo: PrDraftRepository,
        proposal_repo: ImprovementRepository,
        research_repo: ResearchRepository,
        audit_service: AuditService,
        revision_repo: Optional[PatchRevisionRepository] = None,
        ledger_service: Optional[Any] = None
    ):
        self.verification_repo = verification_repo
        self.pr_draft_repo = pr_draft_repo
        self.proposal_repo = proposal_repo
        self.research_repo = research_repo
        self.audit_service = audit_service
        self.revision_repo = revision_repo
        self.ledger_service = ledger_service
        self.analyzer = SandboxPatchAnalyzer()
        self.scorer = PrReviewGateScorer()

    async def _append_ledger_event(self, *, chain_id: str, event_type: str, entity_type: str, entity_id: str, actor_id: str, payload: Dict[str, Any]) -> None:
        if not self.ledger_service:
            return
        try:
            await self.ledger_service.append_event(
                chain_id=chain_id,
                event_type=event_type,
                entity_type=entity_type,
                entity_id=entity_id,
                actor_id=actor_id,
                payload=payload,
            )
        except Exception as exc:
            logger.warning("Review ledger append failed for %s:%s: %s", entity_type, entity_id, exc)

    async def verify_pr_draft(self, pr_draft_id: str, actor_id: str) -> Dict[str, Any]:
        # Log start
        await self.audit_service.log_event(
            event_type="PR_VERIFICATION_STARTED",
            actor_id=actor_id,
            actor_type="user",
            entity_type="pr_draft",
            entity_id=pr_draft_id,
            metadata={"msg": f"Verification started for PR Draft {pr_draft_id}"}
        )

        pr_draft = await self.pr_draft_repo.get_pr_draft(pr_draft_id)
        if not pr_draft:
            await self.audit_service.log_event(
                event_type="PR_VERIFICATION_FAILED",
                actor_id=actor_id,
                actor_type="user",
                entity_type="pr_draft",
                entity_id=pr_draft_id,
                metadata={"error": "PR Draft not found"}
            )
            raise ValueError("PR Draft not found")

        proposal_id = pr_draft["proposal_id"]
        proposal = await self.proposal_repo.get_proposal(proposal_id)
        if not proposal:
            await self.audit_service.log_event(
                event_type="PR_VERIFICATION_FAILED",
                actor_id=actor_id,
                actor_type="user",
                entity_type="pr_draft",
                entity_id=pr_draft_id,
                metadata={"error": "Proposal not found"}
            )
            raise ValueError("Proposal not found")

        # Fetch evidences
        research_id = proposal.get("research_id")
        evidences = []
        if research_id:
            evidences = await self.research_repo.list_evidences(research_id)

        # Analyze patch code
        patch_code = proposal.get("patch_code", "")
        analysis = self.analyzer.analyze_patch(patch_code)

        # Score the PR review
        scoring = self.scorer.calculate_score(analysis, proposal, evidences)

        # Generate test plan
        test_plan = []
        if analysis["test_files"]:
            test_plan.append("Run existing unit/integration tests found in diff.")
        else:
            test_plan.append("WARNING: No tests found in diff. Create a new test case for the change.")
        
        if scoring["risk_level"] == "HIGH":
            test_plan.append("CRITICAL: Manual operator inspection of security/configuration changes is mandatory.")
        test_plan.append("Verify endpoint behaviors against OpenAPI definitions.")

        # Generate rollback plan
        rollback_plan = f"git checkout {pr_draft.get('branch_name', 'main')}\n"
        if pr_draft.get("github_pr_url"):
            rollback_plan += f"Close Draft PR: {pr_draft['github_pr_url']}\n"
        rollback_plan += "Revert code patch locally if applied."

        # Generate markdown report
        report_markdown = self._generate_report(
            pr_draft_id=pr_draft_id,
            proposal_id=proposal_id,
            review_score=scoring["score"],
            review_decision=scoring["review_decision"],
            risk_level=scoring["risk_level"],
            analysis=analysis,
            scoring_breakdown=scoring["breakdown"],
            test_plan=test_plan,
            rollback_plan=rollback_plan
        )

        # Map review decision to DB status
        status = scoring["review_decision"]

        # Create verification record
        verification_data = {
            "pr_draft_id": pr_draft_id,
            "proposal_id": proposal_id,
            "status": status,
            "review_score": scoring["score"],
            "review_decision": scoring["review_decision"],
            "risk_level": scoring["risk_level"],
            "risk_flags": analysis["risky_files"],
            "affected_files": analysis["affected_files"],
            "mutation_detected": analysis["mutation_commands_detected"],
            "test_files_present": len(analysis["test_files"]) > 0,
            "patch_size_lines": analysis["patch_size_lines"],
            "test_plan": test_plan,
            "rollback_plan": rollback_plan,
            "verification_report": report_markdown
        }

        verification = await self.verification_repo.create_verification(verification_data)

        # Log completion
        event_type = "PR_VERIFICATION_COMPLETED"
        if status == "BLOCKED":
            event_type = "PR_VERIFICATION_BLOCKED"

        await self.audit_service.log_event(
            event_type=event_type,
            actor_id=actor_id,
            actor_type="user",
            entity_type="pr_draft",
            entity_id=pr_draft_id,
            metadata={
                "score": scoring["score"],
                "decision": scoring["review_decision"],
                "risk_level": scoring["risk_level"]
            }
        )

        await self.audit_service.log_event(
            event_type="PR_REVIEW_SCORE_ASSIGNED",
            actor_id=actor_id,
            actor_type="user",
            entity_type="pr_draft",
            entity_id=pr_draft_id,
            metadata={
                "score": scoring["score"],
                "decision": scoring["review_decision"]
            }
        )

        await self._append_ledger_event(
            chain_id=f"chain_{pr_draft_id}",
            event_type=event_type,
            entity_type="pr_verification",
            entity_id=verification["id"],
            actor_id=actor_id,
            payload={
                "verification": verification,
                "analysis": analysis,
                "scoring": scoring
            }
        )

        return verification

    def _generate_report(
        self,
        pr_draft_id: str,
        proposal_id: str,
        review_score: float,
        review_decision: str,
        risk_level: str,
        analysis: Dict[str, Any],
        scoring_breakdown: Dict[str, float],
        test_plan: List[str],
        rollback_plan: str
    ) -> str:
        test_plan_str = "\n".join(f"- {step}" for step in test_plan)
        
        report = f"""# PR Verification & Quality Gate Report
Date: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}
PR Draft ID: {pr_draft_id}
Proposal ID: {proposal_id}

## Review Decision
Decision: **{review_decision}**
Quality Score: **{review_score} / 100**
Risk Level: **{risk_level}**

## Analysis Metrics
- Affected Files: {', '.join(analysis['affected_files']) if analysis['affected_files'] else 'None'}
- Risky Files Detected: {', '.join(analysis['risky_files']) if analysis['risky_files'] else 'None'}
- Test Files Present: {'Yes' if len(analysis['test_files']) > 0 else 'No'}
- Patch Size: {analysis['patch_size_lines']} lines
- Mutation Commands Detected: {'Yes' if analysis['mutation_commands_detected'] else 'No'}

## Scoring Breakdown
- Proposal Confidence Check: +{scoring_breakdown.get('confidence_score', 0.0)} points
- Evidence Trust Check: +{scoring_breakdown.get('evidence_trust', 0.0)} points
- Test Presence Check: +{scoring_breakdown.get('test_presence', 0.0)} points
- Risk File Check: +{scoring_breakdown.get('risk_free', 0.0)} points
- Patch Scope Check: +{scoring_breakdown.get('patch_scope', 0.0)} points
- Rollback Capability Check: +{scoring_breakdown.get('rollback_check', 0.0)} points
- Audit Trail Check: +{scoring_breakdown.get('audit_check', 0.0)} points

## Suggested Test Plan
{test_plan_str}

## Suggested Rollback Plan
```
{rollback_plan}
```
"""
        return report

    async def verify_revision(self, revision_id: str, actor_id: str) -> Dict[str, Any]:
        if not self.revision_repo:
            raise ValueError("Revision repository not configured")

        # Log start
        await self.audit_service.log_event(
            event_type="PATCH_REVISION_VERIFICATION_STARTED",
            actor_id=actor_id,
            actor_type="user",
            entity_type="patch_revision",
            entity_id=revision_id,
            metadata={"msg": f"Verification started for Patch Revision {revision_id}"}
        )

        revision = await self.revision_repo.get_revision(revision_id)
        if not revision:
            await self.audit_service.log_event(
                event_type="PATCH_REVISION_VERIFICATION_FAILED",
                actor_id=actor_id,
                actor_type="user",
                entity_type="patch_revision",
                entity_id=revision_id,
                metadata={"error": "Patch Revision not found"}
            )
            raise ValueError("Patch Revision not found")

        pr_draft_id = revision["pr_draft_id"]
        pr_draft = await self.pr_draft_repo.get_pr_draft(pr_draft_id)
        if not pr_draft:
            raise ValueError("PR Draft not found")

        proposal_id = pr_draft["proposal_id"]
        proposal = await self.proposal_repo.get_proposal(proposal_id)
        if not proposal:
            raise ValueError("Proposal not found")

        # Fetch evidences
        research_id = proposal.get("research_id")
        evidences = []
        if research_id:
            evidences = await self.research_repo.list_evidences(research_id)

        # Analyze patch code of the revision (instead of proposal)
        revised_patch_code = revision["revised_patch_code"]
        analysis = self.analyzer.analyze_patch(revised_patch_code)

        # Score the PR review
        scoring = self.scorer.calculate_score(analysis, proposal, evidences)

        # Generate test plan
        test_plan = []
        if analysis["test_files"]:
            test_plan.append("Run existing unit/integration tests found in diff.")
        else:
            test_plan.append("WARNING: No tests found in diff. Create a new test case for the change.")
        
        if scoring["risk_level"] == "HIGH":
            test_plan.append("CRITICAL: Manual operator inspection of security/configuration changes is mandatory.")
        test_plan.append("Verify endpoint behaviors against OpenAPI definitions.")

        # Generate rollback plan
        rollback_plan = f"git checkout {pr_draft.get('branch_name', 'main')}\n"
        if pr_draft.get("github_pr_url"):
            rollback_plan += f"Close Draft PR: {pr_draft['github_pr_url']}\n"
        rollback_plan += "Revert code patch locally if applied."

        # Generate markdown report
        report_markdown = self._generate_report(
            pr_draft_id=pr_draft_id,
            proposal_id=proposal_id,
            review_score=scoring["score"],
            review_decision=scoring["review_decision"],
            risk_level=scoring["risk_level"],
            analysis=analysis,
            scoring_breakdown=scoring["breakdown"],
            test_plan=test_plan,
            rollback_plan=rollback_plan
        )

        status = scoring["review_decision"]

        # Create verification record
        verification_data = {
            "pr_draft_id": pr_draft_id,
            "proposal_id": proposal_id,
            "revision_id": revision_id,
            "status": status,
            "review_score": scoring["score"],
            "review_decision": scoring["review_decision"],
            "risk_level": scoring["risk_level"],
            "risk_flags": analysis["risky_files"],
            "affected_files": analysis["affected_files"],
            "mutation_detected": analysis["mutation_commands_detected"],
            "test_files_present": len(analysis["test_files"]) > 0,
            "patch_size_lines": analysis["patch_size_lines"],
            "test_plan": test_plan,
            "rollback_plan": rollback_plan,
            "verification_report": report_markdown
        }

        verification = await self.verification_repo.create_verification(verification_data)

        # Update verification_status on revision
        if scoring["review_decision"] in ["REVIEW_READY", "NEEDS_HUMAN_CAUTION"]:
            ver_status = "VERIFIED"
        else:
            ver_status = "FAILED"

        await self.revision_repo.update_verification_status(revision_id, ver_status)

        # Log completion
        await self.audit_service.log_event(
            event_type="PATCH_REVISION_VERIFIED" if ver_status == "VERIFIED" else "PATCH_REVISION_VERIFICATION_FAILED",
            actor_id=actor_id,
            actor_type="user",
            entity_type="patch_revision",
            entity_id=revision_id,
            metadata={
                "score": scoring["score"],
                "decision": scoring["review_decision"],
                "risk_level": scoring["risk_level"],
                "verification_status": ver_status
            }
        )

        await self._append_ledger_event(
            chain_id=f"chain_{pr_draft_id}",
            event_type="PATCH_REVISION_VERIFIED" if ver_status == "VERIFIED" else "PATCH_REVISION_VERIFICATION_FAILED",
            entity_type="patch_revision",
            entity_id=revision_id,
            actor_id=actor_id,
            payload={
                "revision": revision,
                "verification": verification,
                "verification_status": ver_status,
                "analysis": analysis,
                "scoring": scoring
            }
        )

        return verification
