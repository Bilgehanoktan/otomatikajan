import uuid
import asyncio
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from apps.bilgeapi.repositories.interface import (
    IncidentRepository,
    DiagnosticRepository,
    FindingRepository,
    RecommendationRepository,
    RepairRequestRepository,
    AuditRepository,
    WebhookDeliveryRepository,
    ReleaseCheckRepository,
    ApiKeyRepository,
    ResearchRepository,
    ImprovementRepository,
    PrDraftRepository,
    PrVerificationRepository,
    PrReviewFeedbackRepository,
    PatchRevisionRepository,
    ReviewLedgerRepository
)
from apps.bilgeapi.schemas.incident import IncidentCreate, IncidentResponse
from apps.bilgeapi.schemas.diagnostic import DiagnosticResult, DiagnosticStatus
from apps.bilgeapi.schemas.repair import RepairRequestCreate, RepairRequestResponse, ApprovalStatus, DispatchStatus
from apps.bilgeapi.schemas.audit import AuditEvent

class MemoryRepositoriesContainer:
    def __init__(self):
        self.incidents: Dict[str, IncidentResponse] = {}
        self.diagnostics: Dict[str, DiagnosticResult] = {}
        self.findings: Dict[str, List[Dict[str, Any]]] = {}
        self.recommendations: Dict[str, List[Dict[str, Any]]] = {}
        self.repair_requests: Dict[str, RepairRequestResponse] = {}
        self.audit_events: List[AuditEvent] = []
        self.webhook_deliveries: List[Dict[str, Any]] = []
        self.release_checks: List[Dict[str, Any]] = []
        self.api_keys: Dict[str, Dict[str, Any]] = {}
        self.research_requests: Dict[str, Dict[str, Any]] = {}
        self.research_evidences: Dict[str, Dict[str, Any]] = {}
        self.improvement_proposals: Dict[str, Dict[str, Any]] = {}
        self.pr_drafts: Dict[str, Dict[str, Any]] = {}
        self.pr_verifications: Dict[str, Dict[str, Any]] = {}
        self.pr_review_feedbacks: Dict[str, Dict[str, Any]] = {}
        self.patch_revisions: Dict[str, Dict[str, Any]] = {}
        self.review_ledger_entries: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    def clear_all(self):
        self.incidents.clear()
        self.diagnostics.clear()
        self.findings.clear()
        self.recommendations.clear()
        self.repair_requests.clear()
        self.audit_events.clear()
        self.webhook_deliveries.clear()
        self.release_checks.clear()
        self.api_keys.clear()
        self.research_requests.clear()
        self.research_evidences.clear()
        self.improvement_proposals.clear()
        self.pr_drafts.clear()
        self.pr_verifications.clear()
        self.pr_review_feedbacks.clear()
        self.patch_revisions.clear()
        self.review_ledger_entries.clear()

memory_repositories = MemoryRepositoriesContainer()


class InMemoryIncidentRepository(IncidentRepository):
    async def create(self, incident: IncidentCreate) -> IncidentResponse:
        async with memory_repositories._lock:
            inc_id = f"inc_{uuid.uuid4().hex[:8]}"
            response = IncidentResponse(
                id=inc_id,
                created_at=datetime.now(timezone.utc),
                **incident.model_dump()
            )
            memory_repositories.incidents[inc_id] = response
            return response

    async def get(self, incident_id: str) -> Optional[IncidentResponse]:
        async with memory_repositories._lock:
            return memory_repositories.incidents.get(incident_id)

    async def list_all(self, project_key: Optional[str] = None) -> List[IncidentResponse]:
        async with memory_repositories._lock:
            all_incidents = list(memory_repositories.incidents.values())
            if project_key:
                return [i for i in all_incidents if i.project_key == project_key]
            return all_incidents


class InMemoryDiagnosticRepository(DiagnosticRepository):
    async def create(self, incident_id: str) -> DiagnosticResult:
        async with memory_repositories._lock:
            diag_id = f"diag_{uuid.uuid4().hex[:8]}"
            result = DiagnosticResult(
                diagnostic_id=diag_id,
                incident_id=incident_id,
                status=DiagnosticStatus.QUEUED,
                created_at=datetime.now(timezone.utc)
            )
            memory_repositories.diagnostics[diag_id] = result
            return result

    async def get(self, diagnostic_id: str) -> Optional[DiagnosticResult]:
        async with memory_repositories._lock:
            return memory_repositories.diagnostics.get(diagnostic_id)

    async def update(self, diagnostic_id: str, status: DiagnosticStatus, **kwargs) -> Optional[DiagnosticResult]:
        async with memory_repositories._lock:
            if diagnostic_id not in memory_repositories.diagnostics:
                return None
            diag = memory_repositories.diagnostics[diagnostic_id]
            
            # Create a copy with updated values
            updated_data = diag.model_dump()
            updated_data["status"] = status
            for k, v in kwargs.items():
                updated_data[k] = v
            
            if status in (DiagnosticStatus.COMPLETED, DiagnosticStatus.FAILED) and not updated_data.get("completed_at"):
                updated_data["completed_at"] = datetime.now(timezone.utc)
                
            updated_diag = DiagnosticResult(**updated_data)
            memory_repositories.diagnostics[diagnostic_id] = updated_diag
            return updated_diag

    async def list_all(self) -> List[DiagnosticResult]:
        async with memory_repositories._lock:
            return list(memory_repositories.diagnostics.values())


class InMemoryFindingRepository(FindingRepository):
    async def create(self, diagnostic_id: str, finding_data: Dict[str, Any]) -> Dict[str, Any]:
        async with memory_repositories._lock:
            if diagnostic_id not in memory_repositories.findings:
                memory_repositories.findings[diagnostic_id] = []
            
            f_id = f"find_{uuid.uuid4().hex[:8]}"
            finding = {"id": f_id, "diagnostic_id": diagnostic_id, **finding_data}
            memory_repositories.findings[diagnostic_id].append(finding)
            return finding

    async def list_by_diagnostic(self, diagnostic_id: str) -> List[Dict[str, Any]]:
        async with memory_repositories._lock:
            return memory_repositories.findings.get(diagnostic_id, [])


class InMemoryRecommendationRepository(RecommendationRepository):
    async def create(self, diagnostic_id: str, recommendation_data: Dict[str, Any]) -> Dict[str, Any]:
        async with memory_repositories._lock:
            if diagnostic_id not in memory_repositories.recommendations:
                memory_repositories.recommendations[diagnostic_id] = []
            
            r_id = f"rec_{uuid.uuid4().hex[:8]}"
            recommendation = {"id": r_id, "diagnostic_id": diagnostic_id, **recommendation_data}
            memory_repositories.recommendations[diagnostic_id].append(recommendation)
            return recommendation

    async def list_by_diagnostic(self, diagnostic_id: str) -> List[Dict[str, Any]]:
        async with memory_repositories._lock:
            return memory_repositories.recommendations.get(diagnostic_id, [])


class InMemoryRepairRequestRepository(RepairRequestRepository):
    async def create(self, diagnostic_id: str, request: RepairRequestCreate) -> RepairRequestResponse:
        async with memory_repositories._lock:
            rep_id = f"rep_{uuid.uuid4().hex[:8]}"
            now = datetime.now(timezone.utc)
            response = RepairRequestResponse(
                id=rep_id,
                diagnostic_id=diagnostic_id,
                requested_by=request.requested_by,
                approved_by=request.approved_by,
                approval_status=request.approval_status,
                risk_score=request.risk_score,
                risk_reason=request.risk_reason,
                dispatch_status=DispatchStatus.PENDING,
                external_reference=None,
                approval_required=request.approval_required,
                rejection_reason=None,
                approved_at=request.approved_at,
                rejected_at=None,
                created_at=now,
                updated_at=now
            )
            memory_repositories.repair_requests[rep_id] = response
            return response

    async def get(self, repair_request_id: str) -> Optional[RepairRequestResponse]:
        async with memory_repositories._lock:
            return memory_repositories.repair_requests.get(repair_request_id)

    async def update(self, repair_request_id: str, approval_status: ApprovalStatus, dispatch_status: DispatchStatus, **kwargs) -> Optional[RepairRequestResponse]:
        async with memory_repositories._lock:
            if repair_request_id not in memory_repositories.repair_requests:
                return None
            rep = memory_repositories.repair_requests[repair_request_id]
            updated_data = rep.model_dump()
            updated_data["approval_status"] = approval_status
            updated_data["dispatch_status"] = dispatch_status
            updated_data["updated_at"] = datetime.now(timezone.utc)
            for k, v in kwargs.items():
                updated_data[k] = v
            
            updated_rep = RepairRequestResponse(**updated_data)
            memory_repositories.repair_requests[repair_request_id] = updated_rep
            return updated_rep

    async def list_all(self) -> List[RepairRequestResponse]:
        async with memory_repositories._lock:
            return list(memory_repositories.repair_requests.values())


class InMemoryAuditRepository(AuditRepository):
    async def write(self, event: AuditEvent) -> None:
        async with memory_repositories._lock:
            memory_repositories.audit_events.append(event)

    async def list_recent(self, limit: int = 100) -> List[AuditEvent]:
        async with memory_repositories._lock:
            # Return last N events ordered by created_at descending
            events = sorted(memory_repositories.audit_events, key=lambda e: e.created_at, reverse=True)
            return events[:limit]


class InMemoryWebhookDeliveryRepository(WebhookDeliveryRepository):
    async def log_delivery(self, delivery_data: Dict[str, Any]) -> None:
        async with memory_repositories._lock:
            delivery_data = delivery_data.copy()
            if "id" not in delivery_data:
                delivery_data["id"] = f"web_{uuid.uuid4().hex[:8]}"
            if "created_at" not in delivery_data:
                delivery_data["created_at"] = datetime.now(timezone.utc)
            memory_repositories.webhook_deliveries.append(delivery_data)

    async def create_delivery(self, delivery_data: Dict[str, Any]) -> Dict[str, Any]:
        async with memory_repositories._lock:
            delivery_data = delivery_data.copy()
            del_id = f"web_{uuid.uuid4().hex[:8]}"
            delivery_data["id"] = del_id
            delivery_data["created_at"] = datetime.now(timezone.utc)
            memory_repositories.webhook_deliveries.append(delivery_data)
            return delivery_data

    async def update_delivery(self, delivery_id: str, delivery_status: str, status_code: Optional[float], error_message: Optional[str], attempt_count: float) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            for item in memory_repositories.webhook_deliveries:
                if item.get("id") == delivery_id:
                    item["delivery_status"] = delivery_status
                    item["status_code"] = status_code
                    item["error_message"] = error_message
                    item["attempt_count"] = attempt_count
                    return item
            return None

    async def get_delivery(self, delivery_id: str) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            for item in memory_repositories.webhook_deliveries:
                if item.get("id") == delivery_id:
                    return item
            return None

    async def list_deliveries(self) -> List[Dict[str, Any]]:
        async with memory_repositories._lock:
            # Sort with fallback if created_at is missing (unlikely)
            return sorted(memory_repositories.webhook_deliveries, key=lambda d: d.get("created_at") or datetime.min.replace(tzinfo=timezone.utc), reverse=True)


class InMemoryReleaseCheckRepository(ReleaseCheckRepository):
    async def create_check(self, check_data: Dict[str, Any]) -> Dict[str, Any]:
        async with memory_repositories._lock:
            check_data = check_data.copy()
            if "id" not in check_data:
                check_data["id"] = f"rel_{uuid.uuid4().hex[:8]}"
            if "created_at" not in check_data:
                check_data["created_at"] = datetime.now(timezone.utc)
            memory_repositories.release_checks.append(check_data)
            return check_data

    async def get_latest_check(self) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            if not memory_repositories.release_checks:
                return None
            sorted_checks = sorted(
                memory_repositories.release_checks,
                key=lambda d: d.get("created_at") or datetime.min.replace(tzinfo=timezone.utc),
                reverse=True
            )
            return sorted_checks[0]

    async def list_checks(self, limit: int = 20) -> List[Dict[str, Any]]:
        async with memory_repositories._lock:
            sorted_checks = sorted(
                memory_repositories.release_checks,
                key=lambda d: d.get("created_at") or datetime.min.replace(tzinfo=timezone.utc),
                reverse=True
            )
            return sorted_checks[:limit]


class InMemoryApiKeyRepository(ApiKeyRepository):
    async def create(self, key_data: Dict[str, Any]) -> Dict[str, Any]:
        async with memory_repositories._lock:
            key_data = key_data.copy()
            if "id" not in key_data:
                key_data["id"] = f"key_{uuid.uuid4().hex[:8]}"
            if "created_at" not in key_data:
                key_data["created_at"] = datetime.now(timezone.utc)
            if "is_active" not in key_data:
                key_data["is_active"] = True
            
            memory_repositories.api_keys[key_data["id"]] = key_data
            return key_data

    async def get(self, key_id: str) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            return memory_repositories.api_keys.get(key_id)

    async def get_by_hash(self, key_hash: str) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            for item in memory_repositories.api_keys.values():
                if item.get("key_hash") == key_hash:
                    return item
            return None

    async def list_all(self) -> List[Dict[str, Any]]:
        async with memory_repositories._lock:
            # Sort by created_at desc
            return sorted(
                memory_repositories.api_keys.values(),
                key=lambda d: d.get("created_at") or datetime.min.replace(tzinfo=timezone.utc),
                reverse=True
            )

    async def revoke(self, key_id: str, revoked_by: str, reason: str) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            item = memory_repositories.api_keys.get(key_id)
            if not item:
                return None
            item["is_active"] = False
            item["revoked_by"] = revoked_by
            item["revoke_reason"] = reason
            item["revoked_at"] = datetime.now(timezone.utc)
            return item

    async def update_last_used(self, key_id: str, last_used: datetime) -> None:
        async with memory_repositories._lock:
            item = memory_repositories.api_keys.get(key_id)
            if item:
                item["last_used_at"] = last_used

    async def update_quota(self, key_id: str, quota_daily: Optional[int], quota_monthly: Optional[int]) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            item = memory_repositories.api_keys.get(key_id)
            if not item:
                return None
            item["quota_daily"] = quota_daily
            item["quota_monthly"] = quota_monthly
            return item


class InMemoryResearchRepository(ResearchRepository):
    async def create_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        async with memory_repositories._lock:
            req_id = f"res_{uuid.uuid4().hex[:8]}"
            response = {
                "id": req_id,
                "incident_id": request_data["incident_id"],
                "query": request_data["query"],
                "status": request_data.get("status", "PENDING"),
                "error_message": request_data.get("error_message"),
                "tenant_id": request_data.get("tenant_id"),
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }
            memory_repositories.research_requests[req_id] = response
            return response

    async def get_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            return memory_repositories.research_requests.get(request_id)

    async def update_request_status(self, request_id: str, status: str, error_message: Optional[str] = None) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            item = memory_repositories.research_requests.get(request_id)
            if not item:
                return None
            item["status"] = status
            if error_message is not None:
                item["error_message"] = error_message
            item["updated_at"] = datetime.now(timezone.utc)
            return item

    async def create_evidence(self, evidence_data: Dict[str, Any]) -> Dict[str, Any]:
        async with memory_repositories._lock:
            ev_id = f"evd_{uuid.uuid4().hex[:8]}"
            response = {
                "id": ev_id,
                "research_id": evidence_data["research_id"],
                "source_url": evidence_data["source_url"],
                "source_domain": evidence_data["source_domain"],
                "title": evidence_data.get("title"),
                "snippet": evidence_data.get("snippet"),
                "raw_content_summary": evidence_data.get("raw_content_summary"),
                "content_hash": evidence_data["content_hash"],
                "trust_score": evidence_data["trust_score"],
                "retrieved_at": datetime.now(timezone.utc),
            }
            memory_repositories.research_evidences[ev_id] = response
            return response

    async def list_evidences(self, research_id: str) -> List[Dict[str, Any]]:
        async with memory_repositories._lock:
            evidences = [
                e for e in memory_repositories.research_evidences.values()
                if e["research_id"] == research_id
            ]
            return sorted(evidences, key=lambda x: x["trust_score"], reverse=True)

    async def get_tenant_daily_research_count(self, tenant_id: str, day: datetime) -> int:
        async with memory_repositories._lock:
            count = 0
            for r in memory_repositories.research_requests.values():
                created = r.get("created_at")
                if r.get("tenant_id") == tenant_id and created:
                    if created.year == day.year and created.month == day.month and created.day == day.day:
                        count += 1
            return count


class InMemoryImprovementRepository(ImprovementRepository):
    async def create_proposal(self, proposal_data: Dict[str, Any]) -> Dict[str, Any]:
        async with memory_repositories._lock:
            prop_id = f"prp_{uuid.uuid4().hex[:8]}"
            response = {
                "id": prop_id,
                "research_id": proposal_data["research_id"],
                "title": proposal_data["title"],
                "rationale": proposal_data["rationale"],
                "patch_code": proposal_data["patch_code"],
                "risk_analysis": proposal_data.get("risk_analysis"),
                "gate_status": proposal_data.get("gate_status", "DRAFT"),
                "gate_score": proposal_data.get("gate_score"),
                "approval_status": proposal_data.get("approval_status", "REVIEW_REQUIRED"),
                "approved_by": None,
                "approved_at": None,
                "ready_for_human_apply": proposal_data.get("ready_for_human_apply", False),
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }
            memory_repositories.improvement_proposals[prop_id] = response
            return response

    async def get_proposal(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            return memory_repositories.improvement_proposals.get(proposal_id)

    async def update_proposal_gate(self, proposal_id: str, gate_status: str, gate_score: Optional[float] = None, risk_analysis: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            item = memory_repositories.improvement_proposals.get(proposal_id)
            if not item:
                return None
            item["gate_status"] = gate_status
            if gate_score is not None:
                item["gate_score"] = gate_score
            if risk_analysis is not None:
                item["risk_analysis"] = risk_analysis
            item["updated_at"] = datetime.now(timezone.utc)
            return item

    async def approve_proposal(self, proposal_id: str, approved_by: str, approved_at: datetime) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            item = memory_repositories.improvement_proposals.get(proposal_id)
            if not item:
                return None
            item["approval_status"] = "APPROVED"
            item["approved_by"] = approved_by
            item["approved_at"] = approved_at
            item["ready_for_human_apply"] = True
            item["updated_at"] = datetime.now(timezone.utc)
            return item

    async def list_proposals(self) -> List[Dict[str, Any]]:
        async with memory_repositories._lock:
            return sorted(
                memory_repositories.improvement_proposals.values(),
                key=lambda x: x.get("created_at") or datetime.min.replace(tzinfo=timezone.utc),
                reverse=True
            )


class InMemoryPrDraftRepository(PrDraftRepository):
    async def create_pr_draft(self, draft_data: Dict[str, Any]) -> Dict[str, Any]:
        async with memory_repositories._lock:
            draft_id = f"prd_{uuid.uuid4().hex[:8]}"
            response = {
                "id": draft_id,
                "proposal_id": draft_data["proposal_id"],
                "provider": draft_data["provider"],
                "status": draft_data.get("status", "PENDING"),
                "github_pr_url": draft_data.get("github_pr_url"),
                "branch_name": draft_data.get("branch_name"),
                "title": draft_data["title"],
                "body": draft_data["body"],
                "evidence_hash": draft_data.get("evidence_hash"),
                "risk_level": draft_data.get("risk_level", "LOW"),
                "risk_flags": draft_data.get("risk_flags"),
                "created_by": draft_data.get("created_by"),
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }
            memory_repositories.pr_drafts[draft_id] = response
            return response

    async def get_pr_draft(self, draft_id: str) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            return memory_repositories.pr_drafts.get(draft_id)

    async def list_pr_drafts_by_proposal(self, proposal_id: str) -> List[Dict[str, Any]]:
        async with memory_repositories._lock:
            return sorted(
                [d for d in memory_repositories.pr_drafts.values() if d["proposal_id"] == proposal_id],
                key=lambda x: x.get("created_at") or datetime.min.replace(tzinfo=timezone.utc),
                reverse=True
            )

    async def update_pr_draft_status(self, draft_id: str, status: str, github_pr_url: Optional[str] = None, error_message: Optional[str] = None) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            item = memory_repositories.pr_drafts.get(draft_id)
            if not item:
                return None
            item["status"] = status
            if github_pr_url is not None:
                item["github_pr_url"] = github_pr_url
            item["updated_at"] = datetime.now(timezone.utc)
            return item


class InMemoryPrVerificationRepository(PrVerificationRepository):
    async def create_verification(self, verification_data: Dict[str, Any]) -> Dict[str, Any]:
        async with memory_repositories._lock:
            ver_id = f"prv_{uuid.uuid4().hex[:8]}"
            response = {
                "id": ver_id,
                "pr_draft_id": verification_data["pr_draft_id"],
                "proposal_id": verification_data["proposal_id"],
                "revision_id": verification_data.get("revision_id"),
                "status": verification_data.get("status", "PENDING"),
                "review_score": verification_data["review_score"],
                "review_decision": verification_data["review_decision"],
                "risk_level": verification_data["risk_level"],
                "risk_flags": verification_data.get("risk_flags"),
                "affected_files": verification_data.get("affected_files"),
                "mutation_detected": verification_data.get("mutation_detected", False),
                "test_files_present": verification_data.get("test_files_present", False),
                "patch_size_lines": verification_data.get("patch_size_lines", 0),
                "test_plan": verification_data.get("test_plan"),
                "rollback_plan": verification_data.get("rollback_plan"),
                "verification_report": verification_data.get("verification_report"),
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }
            memory_repositories.pr_verifications[ver_id] = response
            return response

    async def get_verification_by_pr_draft(self, pr_draft_id: str) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            verifications = [
                v for v in memory_repositories.pr_verifications.values()
                if v["pr_draft_id"] == pr_draft_id
            ]
            if not verifications:
                return None
            return sorted(
                verifications,
                key=lambda x: x.get("created_at") or datetime.min.replace(tzinfo=timezone.utc),
                reverse=True
            )[0]

    async def list_verifications_by_proposal(self, proposal_id: str) -> List[Dict[str, Any]]:
        async with memory_repositories._lock:
            return sorted(
                [v for v in memory_repositories.pr_verifications.values() if v["proposal_id"] == proposal_id],
                key=lambda x: x.get("created_at") or datetime.min.replace(tzinfo=timezone.utc),
                reverse=True
            )

    async def get_verification_by_revision(self, revision_id: str) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            verifications = [
                v for v in memory_repositories.pr_verifications.values()
                if v.get("revision_id") == revision_id
            ]
            if not verifications:
                return None
            return sorted(
                verifications,
                key=lambda x: x.get("created_at") or datetime.min.replace(tzinfo=timezone.utc),
                reverse=True
            )[0]


class InMemoryPrReviewFeedbackRepository(PrReviewFeedbackRepository):
    async def create_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        async with memory_repositories._lock:
            fb_id = f"pfb_{uuid.uuid4().hex[:8]}"
            response = {
                "id": fb_id,
                "pr_draft_id": feedback_data["pr_draft_id"],
                "reviewer_id": feedback_data["reviewer_id"],
                "comment": feedback_data["comment"],
                "status": feedback_data.get("status", "PENDING"),
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
            memory_repositories.pr_review_feedbacks[fb_id] = response
            return response

    async def get_feedback(self, feedback_id: str) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            return memory_repositories.pr_review_feedbacks.get(feedback_id)

    async def list_feedback_by_pr_draft(self, pr_draft_id: str) -> List[Dict[str, Any]]:
        async with memory_repositories._lock:
            feedbacks = [
                fb for fb in memory_repositories.pr_review_feedbacks.values()
                if fb["pr_draft_id"] == pr_draft_id
            ]
            return sorted(
                feedbacks,
                key=lambda x: x.get("created_at") or datetime.min.replace(tzinfo=timezone.utc),
                reverse=True
            )

    async def update_feedback_status(self, feedback_id: str, status: str) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            fb = memory_repositories.pr_review_feedbacks.get(feedback_id)
            if not fb:
                return None
            fb["status"] = status
            fb["updated_at"] = datetime.now(timezone.utc)
            return fb


class InMemoryPatchRevisionRepository(PatchRevisionRepository):
    async def create_revision(self, revision_data: Dict[str, Any]) -> Dict[str, Any]:
        async with memory_repositories._lock:
            rev_id = f"prev_{uuid.uuid4().hex[:8]}"
            response = {
                "id": rev_id,
                "pr_draft_id": revision_data["pr_draft_id"],
                "feedback_id": revision_data.get("feedback_id"),
                "revision_number": revision_data["revision_number"],
                "revised_patch_code": revision_data["revised_patch_code"],
                "risk_analysis": revision_data.get("risk_analysis"),
                "risk_level": revision_data.get("risk_level", "LOW"),
                "verification_status": revision_data.get("verification_status", "PENDING"),
                "created_by": revision_data.get("created_by"),
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
            memory_repositories.patch_revisions[rev_id] = response
            return response

    async def get_revision(self, revision_id: str) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            return memory_repositories.patch_revisions.get(revision_id)

    async def get_latest_revision_number(self, pr_draft_id: str) -> int:
        async with memory_repositories._lock:
            revs = [
                r["revision_number"] for r in memory_repositories.patch_revisions.values()
                if r["pr_draft_id"] == pr_draft_id
            ]
            return max(revs) if revs else 0

    async def list_revisions_by_pr_draft(self, pr_draft_id: str) -> List[Dict[str, Any]]:
        async with memory_repositories._lock:
            revisions = [
                r for r in memory_repositories.patch_revisions.values()
                if r["pr_draft_id"] == pr_draft_id
            ]
            return sorted(
                revisions,
                key=lambda x: x["revision_number"],
                reverse=True
            )

    async def update_verification_status(self, revision_id: str, status: str) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            r = memory_repositories.patch_revisions.get(revision_id)
            if not r:
                return None
            r["verification_status"] = status
            r["updated_at"] = datetime.now(timezone.utc)
            return r


class InMemoryReviewLedgerRepository(ReviewLedgerRepository):
    async def append_entry(self, entry_data: Dict[str, Any]) -> Dict[str, Any]:
        async with memory_repositories._lock:
            entry = entry_data.copy()
            if "id" not in entry:
                entry["id"] = f"rle_{uuid.uuid4().hex[:8]}"
            if "created_at" not in entry:
                entry["created_at"] = datetime.now(timezone.utc)
            memory_repositories.review_ledger_entries[entry["id"]] = entry
            return entry

    async def get_entry(self, entry_id: str) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            return memory_repositories.review_ledger_entries.get(entry_id)

    async def get_latest_entry(self, chain_id: str) -> Optional[Dict[str, Any]]:
        async with memory_repositories._lock:
            entries = [
                entry for entry in memory_repositories.review_ledger_entries.values()
                if entry["chain_id"] == chain_id
            ]
            if not entries:
                return None
            return sorted(entries, key=lambda item: item["sequence_no"], reverse=True)[0]

    async def list_by_chain(self, chain_id: str) -> List[Dict[str, Any]]:
        async with memory_repositories._lock:
            return sorted(
                [
                    entry for entry in memory_repositories.review_ledger_entries.values()
                    if entry["chain_id"] == chain_id
                ],
                key=lambda item: item["sequence_no"]
            )

    async def list_recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        async with memory_repositories._lock:
            return sorted(
                memory_repositories.review_ledger_entries.values(),
                key=lambda item: item.get("created_at") or datetime.min.replace(tzinfo=timezone.utc),
                reverse=True
            )[:limit]

