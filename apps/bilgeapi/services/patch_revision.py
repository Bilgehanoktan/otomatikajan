import logging
from typing import List, Optional, Dict, Any
from apps.bilgeapi.repositories.interface import PrReviewFeedbackRepository, PatchRevisionRepository, PrDraftRepository
from apps.bilgeapi.services.pr_verification import SandboxPatchAnalyzer
from apps.bilgeapi.services.audit import AuditService

logger = logging.getLogger(__name__)

class ReviewerFeedbackService:
    def __init__(self, feedback_repo: PrReviewFeedbackRepository, pr_draft_repo: PrDraftRepository, audit_service: AuditService, ledger_service: Optional[Any] = None):
        self.feedback_repo = feedback_repo
        self.pr_draft_repo = pr_draft_repo
        self.audit_service = audit_service
        self.ledger_service = ledger_service

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
        await self._append_ledger_event(
            chain_id=f"chain_{pr_draft_id}",
            event_type="PR_REVIEW_FEEDBACK_ADDED",
            entity_type="pr_review_feedback",
            entity_id=fb["id"],
            actor_id=actor_id,
            payload=fb
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
        await self._append_ledger_event(
            chain_id=f"chain_{fb['pr_draft_id']}",
            event_type="PR_REVIEW_FEEDBACK_UPDATED",
            entity_type="pr_review_feedback",
            entity_id=feedback_id,
            actor_id=actor_id,
            payload={"before": fb, "after": updated}
        )
        return updated


class PatchRevisionEngine:
    def __init__(self, revision_repo: PatchRevisionRepository, pr_draft_repo: PrDraftRepository, audit_service: AuditService, ledger_service: Optional[Any] = None):
        self.revision_repo = revision_repo
        self.pr_draft_repo = pr_draft_repo
        self.audit_service = audit_service
        self.ledger_service = ledger_service
        self.analyzer = SandboxPatchAnalyzer()

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
        await self._append_ledger_event(
            chain_id=f"chain_{pr_draft_id}",
            event_type="PATCH_REVISION_CREATED",
            entity_type="patch_revision",
            entity_id=rev["id"],
            actor_id=actor_id,
            payload=rev
        )
        return rev

    async def get_revision(self, revision_id: str) -> Optional[Dict[str, Any]]:
        return await self.revision_repo.get_revision(revision_id)

    async def list_revisions_by_pr_draft(self, pr_draft_id: str) -> List[Dict[str, Any]]:
        return await self.revision_repo.list_revisions_by_pr_draft(pr_draft_id)
