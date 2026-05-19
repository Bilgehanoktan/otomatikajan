import logging
import asyncio
from datetime import datetime
from typing import Any, Optional

from libs.db.models.repair_models import UIRepairPRReview, UIRepairPRFinding
from .ui_evidence_runner import UIEvidenceRunner, UIEvidenceRequest
from services.ui_repair.stagehand_adapter import StagehandAdapter
from .ui_diagnosis_models import UIDiagnosisRequest
from .agent_backends.registry import get_backend
from .pr_agent_adapter import PRAgentAdapter
from .repair_models import RepairCase

logger = logging.getLogger(__name__)

class UIRepairOrchestrator:
    """
    Phase 32: Autonomous UI Self-Repair Orchestrator.
    Manages the full lifecycle: Evidence -> Diagnosis -> Patch -> Review -> Governance.
    """

    def __init__(self):
        self.evidence_runner = UIEvidenceRunner()
        self.diagnosis_adapter = StagehandAdapter()
        self.pr_agent = PRAgentAdapter()
        self.backend = get_backend("open_swe")

    async def run_full_repair_cycle(self, case_id: str, target_url: str) -> dict[str, Any]:
        """
        Uçtan uca otonom UI onarım döngüsünü çalıştırır.
        """
        logger.info(f"Starting Phase 32 Repair Cycle for case {case_id} on {target_url}")

        # 1. Evidence Capture
        evidence_req = UIEvidenceRequest(case_id=case_id, target_url=target_url)
        evidence = await self.evidence_runner.capture_evidence(evidence_req)
        logger.info(f"Evidence captured for {case_id}")

        # 2. Diagnosis
        diag_req = UIDiagnosisRequest(
            case_id=case_id, 
            evidence_pack_path=evidence.screenshot_path or "", 
            symptom_description="UI failure detected on page."
        )
        diagnosis = await self.diagnosis_adapter.diagnose(diag_req)
        logger.info(f"Diagnosis completed: {diagnosis.root_cause_summary}")

        # 3. Patch Generation
        repair_case = RepairCase(
            incident_id=case_id,
            summary=diagnosis.root_cause_summary,
            error_type="UI_FAILURE",
            suspected_files=[e.selector for e in diagnosis.suspected_elements],
            context_data={"ui_evidence": evidence.model_dump_json()}
        )
        
        # For Phase 32, we use a temporary sandbox directory if available
        # In a real environment, this would be a fresh clone
        sandbox_path = f"repair_outputs/{case_id}/sandbox"
        import os
        os.makedirs(sandbox_path, exist_ok=True)

        patch_result = self.backend.generate_patch(repair_case, work_dir=sandbox_path)
        
        if patch_result.exit_status == "blocked":
            logger.warning(f"Repair blocked for {case_id}: {patch_result.agent_summary}")
            return {
                "case_id": case_id,
                "final_status": "DRAFT_PR_BLOCKED_SANDBOX_REQUIRED",
                "detail": patch_result.agent_summary
            }

        logger.info(f"Patch generated with confidence {patch_result.confidence}")

        # 4. PR-Agent Review (Governance Gate)
        # For Phase 32, we assume a PR is created. In production, this URL would come from the VCS adapter.
        pr_url = f"https://github.com/Sovereign-AGI/sovereign-control-plane/pull/{case_id}"
        review_result = await self.pr_agent.run_full_review_cycle(case_id, pr_url)
        logger.info(f"PR-Agent review finished: {review_result.governance_decision}")

        return {
            "case_id": case_id,
            "evidence": evidence,
            "diagnosis": diagnosis,
            "patch": patch_result,
            "review": review_result,
            "final_status": review_result.governance_decision
        }
