import os
import json
import uuid
from datetime import datetime
from typing import Optional, Set, Dict

from services.self_repair_audit.action_models import SuggestionActionRequest, SuggestionActionLog
from services.self_repair_audit.suggestion_store import (
    load_suggestion_states,
    update_suggestion_state,
    record_action_log,
    get_audit_run_dir,
)

ALLOWED_TRANSITIONS: Dict[str, Set[str]] = {
    "NEW": {
        "APPROVED_FOR_REPAIR",
        "APPROVED_FOR_PROJECT_FACTORY",
        "WAR_ROOM_RECOMMENDED",
        "DEFERRED",
        "REJECTED",
        "MORE_EVIDENCE_REQUESTED",
    },
    "DEFERRED": {
        "APPROVED_FOR_REPAIR",
        "APPROVED_FOR_PROJECT_FACTORY",
    },
    "MORE_EVIDENCE_REQUESTED": {
        "APPROVED_FOR_REPAIR",
        "REJECTED",
    },
    "APPROVED_FOR_REPAIR": {
        "IN_PROGRESS",
    },
}

def get_finding_details(audit_run_id: str, suggestion_id: str, workspace_root: Optional[str] = None) -> Optional[dict]:
    """
    Finds and returns the full finding details of a given finding within the audit run files.
    """
    run_dir = get_audit_run_dir(audit_run_id, workspace_root)
    classified_file = os.path.join(run_dir, "classified_findings.json")
    report_file = os.path.join(run_dir, "audit_report.json")
    
    findings = []
    if os.path.exists(classified_file):
        with open(classified_file, "r", encoding="utf-8") as f:
            findings = json.load(f).get("findings", [])
    elif os.path.exists(report_file):
        with open(report_file, "r", encoding="utf-8") as f:
            findings = json.load(f).get("findings", [])
            
    for f in findings:
        if isinstance(f, dict):
            fid = f.get("finding_id")
            if fid == suggestion_id:
                return f
        else:
            fid = getattr(f, "finding_id", None)
            if fid == suggestion_id:
                return {k: getattr(f, k) for k in dir(f) if not k.startswith("_")}
                
    return None

def get_finding_severity(audit_run_id: str, suggestion_id: str, workspace_root: Optional[str] = None) -> str:
    """
    Finds and returns the severity level of a given finding within the audit run files.
    """
    f = get_finding_details(audit_run_id, suggestion_id, workspace_root)
    if f:
        sev = f.get("severity", "INFO")
        return (sev or "INFO").upper()
    return "INFO"

def process_suggestion_action(
    audit_run_id: str,
    suggestion_id: str,
    action: str,
    to_status: str,
    req: SuggestionActionRequest,
    workspace_root: Optional[str] = None,
) -> SuggestionActionLog:
    """
    Validates input parameters, checks allowed state transitions, checks risk acknowledgement
    for Critical/High severity findings, records the action log, and persists status updates.
    """
    # 1. Basic validation
    if not req.operator_id or not req.operator_id.strip():
        raise ValueError("operator_id cannot be empty.")
    if not req.rationale or not req.rationale.strip():
        raise ValueError("rationale cannot be empty.")
        
    # 2. Check existence in the suggestion states mapping
    states = load_suggestion_states(audit_run_id, workspace_root)
    if suggestion_id not in states:
        raise KeyError(f"Suggestion ID '{suggestion_id}' not found in audit run '{audit_run_id}'.")
        
    from_status = states[suggestion_id]
    
    # 3. Check redundant transitions
    if from_status == to_status:
        raise ValueError(f"Suggestion '{suggestion_id}' is already in status '{to_status}'.")
        
    # 4. Check transition logic
    allowed = ALLOWED_TRANSITIONS.get(from_status, set())
    if to_status not in allowed:
        raise ValueError(f"Transition from '{from_status}' to '{to_status}' is forbidden.")
        
    # 5. Check risk acknowledgement rules for CRITICAL/HIGH findings
    severity = get_finding_severity(audit_run_id, suggestion_id, workspace_root)
    if severity in ("CRITICAL", "HIGH") and not req.risk_acknowledgement:
        raise ValueError(f"Risk acknowledgement is mandatory for {severity} severity findings.")
        
    # 6. Generate action logs
    action_id = f"ACT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    created_at = datetime.utcnow().isoformat() + "Z"
    
    # Format a dummy next step message for this phase
    step_msg = "Faz 4 bridge will convert this to repair case" if to_status == "APPROVED_FOR_REPAIR" else \
               "Faz 5 bridge will convert this to project factory task" if to_status == "APPROVED_FOR_PROJECT_FACTORY" else \
               "Action recorded successfully"
               
    log = SuggestionActionLog(
        action_id=action_id,
        suggestion_id=suggestion_id,
        action=action,
        from_status=from_status,
        to_status=to_status,
        operator_id=req.operator_id,
        rationale=req.rationale,
        risk_acknowledgement=req.risk_acknowledgement,
        created_at=created_at,
        result={
            "repair_case_created": False,
            "next_step": step_msg
        }
    )
    
    # 7. Commit changes and write artifacts
    record_action_log(audit_run_id, log, workspace_root)
    update_suggestion_state(audit_run_id, suggestion_id, to_status, workspace_root)
    
    return log
