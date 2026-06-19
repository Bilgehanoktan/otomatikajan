import logging
from typing import Any, Dict, Optional

from apps.bilgeapi.config import settings
from apps.bilgeapi.repositories.interface import (
    AIPatchSuggestionRepository,
    ImprovementRepository,
    PatchRevisionRepository,
    PrDraftRepository,
    PrReviewFeedbackRepository,
    ResearchRepository,
)
from apps.bilgeapi.services.pr_verification import SandboxPatchAnalyzer
from apps.bilgeapi.services.review_ledger import CanonicalPayloadHasher, PayloadRedactor


logger = logging.getLogger(__name__)


class PatchSuggestionContextBuilder:
    def __init__(
        self,
        *,
        pr_draft_repo: PrDraftRepository,
        proposal_repo: ImprovementRepository,
        feedback_repo: PrReviewFeedbackRepository,
        revision_repo: PatchRevisionRepository,
        research_repo: ResearchRepository,
        ledger_service: Optional[Any] = None,
    ):
        self.pr_draft_repo = pr_draft_repo
        self.proposal_repo = proposal_repo
        self.feedback_repo = feedback_repo
        self.revision_repo = revision_repo
        self.research_repo = research_repo
        self.ledger_service = ledger_service
        self.redactor = PayloadRedactor()

    async def build_context(
        self,
        *,
        pr_draft_id: str,
        feedback_id: Optional[str],
        revision_id: Optional[str],
        instruction: str,
    ) -> Dict[str, Any]:
        pr_draft = await self.pr_draft_repo.get_pr_draft(pr_draft_id)
        if not pr_draft:
            raise ValueError("PR Draft not found")

        proposal = await self.proposal_repo.get_proposal(pr_draft["proposal_id"])
        if not proposal:
            raise ValueError("Proposal not found")

        feedback = None
        if feedback_id:
            feedback = await self.feedback_repo.get_feedback(feedback_id)
            if not feedback or feedback["pr_draft_id"] != pr_draft_id:
                raise ValueError("Feedback not found for PR Draft")

        revision = None
        if revision_id:
            revision = await self.revision_repo.get_revision(revision_id)
            if not revision or revision["pr_draft_id"] != pr_draft_id:
                raise ValueError("Patch Revision not found for PR Draft")

        evidences = []
        if proposal.get("research_id"):
            evidences = await self.research_repo.list_evidences(proposal["research_id"])

        ledger_summary = []
        if self.ledger_service:
            try:
                ledger_entries = await self.ledger_service.list_chain(f"chain_{pr_draft_id}")
                ledger_summary = [
                    {
                        "sequence_no": entry.get("sequence_no"),
                        "event_type": entry.get("event_type"),
                        "entity_type": entry.get("entity_type"),
                        "entity_id": entry.get("entity_id"),
                        "payload_hash": entry.get("payload_hash"),
                        "event_hash": entry.get("event_hash"),
                    }
                    for entry in ledger_entries[-10:]
                ]
            except Exception as exc:
                logger.warning("Unable to load review ledger context for %s: %s", pr_draft_id, exc)

        context = {
            "instruction": instruction,
            "pr_draft": pr_draft,
            "proposal": proposal,
            "feedback": feedback,
            "revision": revision,
            "evidences": evidences,
            "review_ledger_chain": ledger_summary,
        }
        redacted = self.redactor.redact(context)
        canonical = CanonicalPayloadHasher.canonicalize(redacted)
        max_chars = settings.BILGEAPI_AI_PATCH_MAX_CONTEXT_CHARS
        if len(canonical) > max_chars:
            redacted = {
                "instruction": instruction,
                "pr_draft": {"id": pr_draft["id"], "proposal_id": pr_draft["proposal_id"]},
                "proposal": {
                    "id": proposal["id"],
                    "research_id": proposal.get("research_id"),
                    "risk_analysis": proposal.get("risk_analysis"),
                    "gate_status": proposal.get("gate_status"),
                    "approval_status": proposal.get("approval_status"),
                },
                "feedback": {"id": feedback.get("id"), "status": feedback.get("status")} if feedback else None,
                "revision": {"id": revision.get("id"), "risk_level": revision.get("risk_level")} if revision else None,
                "evidence_count": len(evidences),
                "review_ledger_entries": len(ledger_summary),
                "truncated": True,
            }
        return redacted


class AIPatchSuggestionService:
    def __init__(
        self,
        *,
        suggestion_repo: AIPatchSuggestionRepository,
        pr_draft_repo: PrDraftRepository,
        feedback_repo: PrReviewFeedbackRepository,
        revision_repo: PatchRevisionRepository,
        context_builder: PatchSuggestionContextBuilder,
        provider: Any,
        verification_service: Any,
        ledger_service: Optional[Any] = None,
    ):
        self.suggestion_repo = suggestion_repo
        self.pr_draft_repo = pr_draft_repo
        self.feedback_repo = feedback_repo
        self.revision_repo = revision_repo
        self.context_builder = context_builder
        self.provider = provider
        self.verification_service = verification_service
        self.ledger_service = ledger_service
        self.redactor = PayloadRedactor()
        self.hasher = CanonicalPayloadHasher()
        self.analyzer = SandboxPatchAnalyzer()

    def compute_prompt_hash(self, context: Dict[str, Any], instruction: str) -> str:
        redacted = self.redactor.redact({"context": context, "instruction": instruction})
        return self.hasher.hash_payload(redacted)

    async def generate_suggestion(
        self,
        *,
        pr_draft_id: str,
        feedback_id: Optional[str],
        revision_id: Optional[str],
        instruction: str,
        actor_id: str,
    ) -> Dict[str, Any]:
        context = await self.context_builder.build_context(
            pr_draft_id=pr_draft_id,
            feedback_id=feedback_id,
            revision_id=revision_id,
            instruction=instruction,
        )
        prompt_hash = self.compute_prompt_hash(context, instruction)
        provider_result = await self.provider.generate_patch_suggestion(context)
        suggested_patch_code = provider_result.get("suggested_patch_code") or ""
        if not suggested_patch_code.strip():
            raise ValueError("AI patch provider returned an empty patch suggestion")
        if len(suggested_patch_code) > settings.BILGEAPI_AI_PATCH_MAX_OUTPUT_CHARS:
            raise ValueError("AI patch suggestion exceeds output size limit")

        analysis = self.analyzer.analyze_patch(suggested_patch_code)
        risk_level = "HIGH" if analysis["risky_files"] else "LOW"

        suggestion = await self.suggestion_repo.create_suggestion(
            {
                "pr_draft_id": pr_draft_id,
                "feedback_id": feedback_id,
                "revision_id": revision_id,
                "provider": getattr(self.provider, "provider_name", settings.BILGEAPI_AI_PATCH_PROVIDER),
                "model_name": getattr(self.provider, "model_name", settings.BILGEAPI_AI_PATCH_MODEL),
                "prompt_hash": prompt_hash,
                "context_summary": context,
                "suggested_patch_code": suggested_patch_code,
                "rationale": provider_result.get("rationale"),
                "risk_notes": provider_result.get("risk_notes"),
                "risk_level": risk_level,
                "status": "GENERATED",
                "created_by": actor_id,
            }
        )
        await self._append_ledger_event(
            pr_draft_id=pr_draft_id,
            event_type="AI_PATCH_SUGGESTION_GENERATED",
            entity_id=suggestion["id"],
            actor_id=actor_id,
            payload={"suggestion": suggestion, "analysis": analysis},
        )
        return suggestion

    async def verify_suggestion(self, suggestion_id: str, actor_id: str) -> Dict[str, Any]:
        verification = await self.verification_service.verify_ai_suggestion(suggestion_id, actor_id)
        status = self._status_from_decision(verification["review_decision"])
        updated = await self.suggestion_repo.attach_verification(
            suggestion_id=suggestion_id,
            verification_id=verification["id"],
            risk_level=verification["risk_level"],
            status=status,
        )
        if not updated:
            raise ValueError("AI Patch Suggestion not found")
        await self._append_ledger_event(
            pr_draft_id=verification["pr_draft_id"],
            event_type="AI_PATCH_SUGGESTION_VERIFIED" if status == "VERIFIED" else "AI_PATCH_SUGGESTION_BLOCKED",
            entity_id=suggestion_id,
            actor_id=actor_id,
            payload={"suggestion": updated, "verification": verification},
        )
        return verification

    async def accept_for_review(self, suggestion_id: str, actor_id: str) -> Dict[str, Any]:
        suggestion = await self.suggestion_repo.get_suggestion(suggestion_id)
        if not suggestion:
            raise ValueError("AI Patch Suggestion not found")
        if suggestion["status"] not in {"VERIFIED", "NEEDS_REVISION"}:
            raise ValueError("Only verified suggestions can be accepted for review")
        updated = await self.suggestion_repo.update_suggestion_status(suggestion_id, "ACCEPTED_FOR_REVIEW")
        await self._append_ledger_event(
            pr_draft_id=suggestion["pr_draft_id"],
            event_type="AI_PATCH_SUGGESTION_ACCEPTED_FOR_REVIEW",
            entity_id=suggestion_id,
            actor_id=actor_id,
            payload={"suggestion": updated},
        )
        return updated

    async def reject_suggestion(self, suggestion_id: str, *, reason: Optional[str], actor_id: str) -> Dict[str, Any]:
        suggestion = await self.suggestion_repo.get_suggestion(suggestion_id)
        if not suggestion:
            raise ValueError("AI Patch Suggestion not found")
        updated = await self.suggestion_repo.update_suggestion_status(suggestion_id, "REJECTED")
        await self._append_ledger_event(
            pr_draft_id=suggestion["pr_draft_id"],
            event_type="AI_PATCH_SUGGESTION_REJECTED",
            entity_id=suggestion_id,
            actor_id=actor_id,
            payload={"suggestion": updated, "reason": reason},
        )
        return updated

    async def list_suggestions(self, pr_draft_id: str) -> list[Dict[str, Any]]:
        return await self.suggestion_repo.list_suggestions_by_pr_draft(pr_draft_id)

    async def get_suggestion(self, suggestion_id: str) -> Dict[str, Any]:
        suggestion = await self.suggestion_repo.get_suggestion(suggestion_id)
        if not suggestion:
            raise ValueError("AI Patch Suggestion not found")
        return suggestion

    def _status_from_decision(self, review_decision: str) -> str:
        if review_decision in {"REVIEW_READY", "NEEDS_HUMAN_CAUTION"}:
            return "VERIFIED"
        if review_decision == "NEEDS_REVISION":
            return "NEEDS_REVISION"
        return "BLOCKED"

    async def _append_ledger_event(
        self,
        *,
        pr_draft_id: str,
        event_type: str,
        entity_id: str,
        actor_id: str,
        payload: Dict[str, Any],
    ) -> None:
        if not self.ledger_service:
            return
        try:
            await self.ledger_service.append_event(
                chain_id=f"chain_{pr_draft_id}",
                event_type=event_type,
                entity_type="ai_patch_suggestion",
                entity_id=entity_id,
                actor_id=actor_id,
                payload=payload,
            )
        except Exception as exc:
            logger.warning("Review ledger append failed for AI suggestion %s: %s", entity_id, exc)
