from typing import Dict, Any, Optional, cast
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from libs.db.models.ui_repair_models import UIRepairCase, UIRepairAttempt, UIRepairStatus, RepairAttemptStatus
from .stagehand_adapter import StagehandAdapter
from .open_swe_adapter import OpenSWEAdapter
from .repair_state_machine import UIRepairStateMachine
from .repair_evidence_writer import UIRepairEvidenceWriter
from .pr_agent_adapter import PRAgentAdapter
from .verifier_mesh_adapter import VerifierMeshAdapter
from .changed_file_risk_classifier import ChangedFileRiskClassifier
from .governance_adapter import GovernanceAdapter
from services.observability.logging import get_logger

_log = get_logger("ui_repair_orchestrator")

class UIRepairOrchestrator:
    """
    Phase 4: Hardened Orchestrator for UI Repair.
    Manages the Stagehand -> OpenSWE pipeline with strict state tracking.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.stagehand = StagehandAdapter()
        self.openswe = OpenSWEAdapter()
        self.pr_agent = PRAgentAdapter()
        self.verifier = VerifierMeshAdapter()
        self.governance = GovernanceAdapter()
        self.evidence = UIRepairEvidenceWriter(db)

    async def run_repair_cycle(self, case_id: UUID) -> Dict[str, Any]:
        """
        Executes the full autonomous repair cycle.
        """
        # 1. Fetch and validate case
        stmt = select(UIRepairCase).where(UIRepairCase.id == case_id)
        case_obj = (await self.db.execute(stmt)).scalar_one_or_none()
        if not case_obj:
            return {"status": "error", "message": "Case not found"}
            
        case = cast(Any, case_obj)

        can_start, error = UIRepairStateMachine.validate_attempt_start(case)
        if not can_start:
            return {"status": "error", "message": error}

        # 2. Create Repair Attempt
        attempt_no = len(case.attempts) + 1
        attempt_obj = UIRepairAttempt(
            case_id=case.id,
            attempt_no=attempt_no,
            status=RepairAttemptStatus.STARTED.value
        )
        self.db.add(attempt_obj)
        case.status = UIRepairStatus.REPAIRING.value
        await self.db.commit()
        await self.db.refresh(attempt_obj)
        
        attempt = cast(Any, attempt_obj)

        await self.evidence.log_event(
            case_id=case_id,
            attempt_id=attempt.id,
            event_type="REPAIR_CYCLE_STARTED",
            status="SUCCESS",
            message=f"Starting repair attempt #{attempt_no}"
        )

        try:
            # 3. Stagehand Diagnostic
            attempt.status = RepairAttemptStatus.STAGEHAND_RUNNING.value
            await self.db.commit()
            
            diagnostic = await self.stagehand.diagnose({
                "route": str(case.route),
                "failure_type": str(case.failure_type),
                "console_errors": case.console_errors_json,
                "network_errors": case.network_errors_json
            })
            
            await self.evidence.record_stagehand_diagnostic(attempt_obj, diagnostic)
            attempt.status = RepairAttemptStatus.STAGEHAND_COMPLETED.value
            await self.db.commit()

            # 4. OpenSWE Repair
            attempt.status = RepairAttemptStatus.OPEN_SWE_RUNNING.value
            await self.db.commit()
            
            repair_result = await self.openswe.generate_repair(str(case.id), diagnostic)
            
            await self.evidence.record_open_swe_result(attempt_obj, repair_result)
            
            if repair_result.get("success"):
                attempt.status = RepairAttemptStatus.PR_OPENED.value
                case.status = UIRepairStatus.PR_OPENED.value
                case.pr_url = repair_result.get("pr_url")
                case.patch_path = repair_result.get("patch_path")
                case.repair_summary = repair_result.get("patch_summary")
                await self.db.commit()

                # Phase 5: PR-Agent Review Gate
                attempt.status = RepairAttemptStatus.REVIEW_RUNNING.value
                await self.db.commit()
                
                review_res = await self.pr_agent.run_review_pipeline(str(case.pr_url), str(case.id))
                await self.evidence.record_pr_review(attempt_obj, review_res)
                
                # Phase 5: Verifier Mesh Gate
                attempt.status = RepairAttemptStatus.VERIFIER_RUNNING.value
                await self.db.commit()
                
                verifier_res = await self.verifier.run_verification_gates(str(case.pr_url), str(case.id))
                await self.evidence.record_verifier_run(attempt_obj, verifier_res)
                
                # Phase 5: Risk Classification & Governance Policy
                risk_data = ChangedFileRiskClassifier.classify(review_res.get("changed_files", []))
                
                # Create Approval Request
                gov_res = await self.governance.create_approval_request(
                    str(case.id), 
                    str(attempt.id),
                    risk_data,
                    str(review_res.get("status")),
                    str(verifier_res.get("status"))
                )
                await self.evidence.record_governance_request(attempt_obj, gov_res)
                
                # Transition to WAITING_GOVERNANCE
                case.status = UIRepairStatus.WAITING_GOVERNANCE.value
                attempt.status = RepairAttemptStatus.WAITING_GOVERNANCE.value
            else:
                attempt.status = RepairAttemptStatus.FAILED.value
                case.status = UIRepairStatus.REPAIR_FAILED.value

            attempt.finished_at = datetime.now()
            await self.db.commit()
            
            return {
                "status": "success",
                "attempt_id": str(attempt.id),
                "final_status": str(attempt.status)
            }

        except Exception as e:
            _log.error(f"Repair cycle failed for case {case_id}: {e}")
            attempt.status = RepairAttemptStatus.FAILED.value
            attempt.error_message = str(e)
            attempt.finished_at = datetime.now()
            case.status = UIRepairStatus.REPAIR_FAILED.value
            
            await self.evidence.log_event(
                case_id=case_id,
                attempt_id=attempt.id,
                event_type="REPAIR_CYCLE_CRASHED",
                status="ERROR",
                message=str(e)
            )
            await self.db.commit()
            return {"status": "error", "message": str(e)}
