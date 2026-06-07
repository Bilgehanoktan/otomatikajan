from typing import List, Optional, Dict, Any
from apps.bilgeapi.repositories.interface import PrReviewFeedbackRepository, PatchRevisionRepository, PrDraftRepository
from apps.bilgeapi.services.pr_verification import SandboxPatchAnalyzer
from apps.bilgeapi.services.audit import AuditService

class ReviewerFeedbackService:
    def __init__(self, feedback_repo: PrReviewFeedbackRepository, pr_draft_repo: PrDraftRepository, audit_service: AuditService):
        self.feedback_repo = feedback_repo
        self.pr_draft_repo = pr_draft_repo
        self.audit_service = audit_service

    async def add_feedback(self, pr_draft_id: str, comment: str, reviewer_id: str, actor_id: str) -> Dict[str, Any]:
        pr_draft = await self.pr_draft_repo.get_pr_draft(pr_draft_id)
        if not pr_draft:
            raise ValueError("PR Draft not found")
        
        feedback_data = {
            "pr_draft_id": pr_draft_id,
            "reviewer_id": reviewer_id,
            "comment": comment,
            "status": "PENDING"
        }
        fb = await self.feedback_repo.create_feedback(feedback_data)
        
        await self.audit_service.log_event(
            event_type="PR_REVIEW_FEEDBACK_ADDED",
            actor_id=actor_id,
            actor_type="user",
            entity_type="pr_draft",
            entity_id=pr_draft_id,
            metadata={"feedback_id": fb["id"], "reviewer_id": reviewer_id}
        )
        return fb

    async def get_feedback(self, feedback_id: str) -> Optional[Dict[str, Any]]:
        return await self.feedback_repo.get_feedback(feedback_id)

    async def list_feedback_by_pr_draft(self, pr_draft_id: str) -> List[Dict[str, Any]]:
        return await self.feedback_repo.list_feedback_by_pr_draft(pr_draft_id)

    async def update_feedback_status(self, feedback_id: str, new_status: str, actor_id: str) -> Dict[str, Any]:
        fb = await self.feedback_repo.get_feedback(feedback_id)
        if not fb:
            raise ValueError("Feedback not found")
        
        current_status = fb["status"]
        if new_status not in ["PENDING", "RESOLVED", "SUPERSEDED"]:
            raise ValueError(f"Invalid status: {new_status}")
            
        if current_status in ["RESOLVED", "SUPERSEDED"]:
            raise ValueError(f"Cannot transition from closed status '{current_status}' to '{new_status}'")
            
        updated = await self.feedback_repo.update_feedback_status(feedback_id, new_status)
        
        await self.audit_service.log_event(
            event_type="PR_REVIEW_FEEDBACK_UPDATED",
            actor_id=actor_id,
            actor_type="user",
            entity_type="pr_draft",
            entity_id=fb["pr_draft_id"],
            metadata={"feedback_id": feedback_id, "old_status": current_status, "new_status": new_status}
        )
        return updated


class PatchRevisionEngine:
    def __init__(self, revision_repo: PatchRevisionRepository, pr_draft_repo: PrDraftRepository, audit_service: AuditService):
        self.revision_repo = revision_repo
        self.pr_draft_repo = pr_draft_repo
        self.audit_service = audit_service
        self.analyzer = SandboxPatchAnalyzer()

    async def create_revision(self, pr_draft_id: str, feedback_id: Optional[str], revised_patch_code: str, actor_id: str) -> Dict[str, Any]:
        pr_draft = await self.pr_draft_repo.get_pr_draft(pr_draft_id)
        if not pr_draft:
            raise ValueError("PR Draft not found")

        latest_num = await self.revision_repo.get_latest_revision_number(pr_draft_id)
        next_num = latest_num + 1

        analysis = self.analyzer.analyze_patch(revised_patch_code)
        
        patch_size = analysis.get("patch_size_lines", 0)
        if len(analysis.get("risky_files", [])) > 0 or analysis.get("mutation_commands_detected", False):
            risk_level = "HIGH"
        elif patch_size > 100 or len(analysis.get("affected_files", [])) > 3:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        revision_data = {
            "pr_draft_id": pr_draft_id,
            "feedback_id": feedback_id,
            "revision_number": next_num,
            "revised_patch_code": revised_patch_code,
            "risk_analysis": analysis,
            "risk_level": risk_level,
            "verification_status": "PENDING",
            "created_by": actor_id
        }
        
        rev = await self.revision_repo.create_revision(revision_data)

        await self.audit_service.log_event(
            event_type="PATCH_REVISION_GENERATED",
            actor_id=actor_id,
            actor_type="user",
            entity_type="pr_draft",
            entity_id=pr_draft_id,
            metadata={"revision_id": rev["id"], "revision_number": next_num}
        )
        return rev

    async def get_revision(self, revision_id: str) -> Optional[Dict[str, Any]]:
        return await self.revision_repo.get_revision(revision_id)

    async def list_revisions_by_pr_draft(self, pr_draft_id: str) -> List[Dict[str, Any]]:
        return await self.revision_repo.list_revisions_by_pr_draft(pr_draft_id)
