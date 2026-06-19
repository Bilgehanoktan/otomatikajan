from typing import Tuple, List, Optional
from libs.db.models.ui_repair_models import UIRepairStatus, RepairAttemptStatus, UIRepairCase, UIRepairAttempt
from services.observability.logging import get_logger

_log = get_logger("ui_repair_state_machine")

class UIRepairStateMachine:
    """
    Phase 4: Strict State Machine for UI Repair Process.
    Ensures valid transitions and prevents concurrent conflicting attempts.
    """

    # Case Transitions (Using string values for compatibility)
    VALID_CASE_TRANSITIONS = {
        UIRepairStatus.DETECTED.value: [UIRepairStatus.EVIDENCE_CAPTURED.value, UIRepairStatus.IGNORED.value],
        UIRepairStatus.EVIDENCE_CAPTURED.value: [UIRepairStatus.READY_FOR_STAGEHAND.value, UIRepairStatus.IGNORED.value],
        UIRepairStatus.READY_FOR_STAGEHAND.value: [UIRepairStatus.REPAIRING.value, UIRepairStatus.IGNORED.value],
        UIRepairStatus.REPAIRING.value: [UIRepairStatus.PATCH_GENERATED.value, UIRepairStatus.REPAIR_FAILED.value],
        UIRepairStatus.PATCH_GENERATED.value: [UIRepairStatus.PR_OPENED.value, UIRepairStatus.REPAIR_FAILED.value],
        UIRepairStatus.PR_OPENED.value: [UIRepairStatus.WAITING_GOVERNANCE.value, UIRepairStatus.REPAIR_FAILED.value],
        UIRepairStatus.WAITING_GOVERNANCE.value: [UIRepairStatus.RESOLVED.value, UIRepairStatus.REPAIR_FAILED.value],
        UIRepairStatus.REPAIR_FAILED.value: [UIRepairStatus.REPAIRING.value, UIRepairStatus.MANUAL_REVIEW_REQUIRED.value],
    }

    @staticmethod
    def can_transition_case(current_status: str, next_status: str) -> bool:
        valid_next = UIRepairStateMachine.VALID_CASE_TRANSITIONS.get(current_status, [])
        return next_status in valid_next

    @staticmethod
    def validate_attempt_start(case: UIRepairCase) -> Tuple[bool, Optional[str]]:
        """Checks if a new repair attempt can be started for the case."""
        if case.status == UIRepairStatus.REPAIRING:
            # Check if there's actually a running attempt
            for attempt in case.attempts:
                if attempt.status not in [RepairAttemptStatus.COMPLETED, RepairAttemptStatus.FAILED, RepairAttemptStatus.CANCELLED]:
                    return False, "An active repair attempt is already in progress."
        
        if case.status in [UIRepairStatus.RESOLVED, UIRepairStatus.IGNORED]:
            return False, f"Cannot start repair for a case in {case.status} status."
            
        return True, None

    @staticmethod
    def validate_patch_completion(attempt: UIRepairAttempt) -> Tuple[bool, Optional[str]]:
        if not attempt.patch_path and not attempt.patch_summary:
            return False, "Patch data (path or summary) is required to complete patch generation."
        return True, None

    @staticmethod
    def validate_pr_completion(attempt: UIRepairAttempt) -> Tuple[bool, Optional[str]]:
        if not attempt.pr_url:
            return False, "PR URL is required to transition to PR_OPENED status."
        return True, None
