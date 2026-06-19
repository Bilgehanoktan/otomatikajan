import os
import json
from typing import Dict, Any, List, Optional
from services.self_repair_audit.action_models import SuggestionActionLog

def get_workspace_root(workspace_root: Optional[str] = None) -> str:
    if workspace_root:
        return workspace_root
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_audit_run_dir(audit_run_id: str, workspace_root: Optional[str] = None) -> str:
    root = get_workspace_root(workspace_root)
    return os.path.join(root, "project_outputs", "audit_runs", audit_run_id)

def load_suggestion_states(audit_run_id: str, workspace_root: Optional[str] = None) -> Dict[str, str]:
    """
    Loads suggestion statuses from suggestion_state.json.
    If not found, initializes it using classified_findings.json or audit_report.json findings,
    marking them as 'NEW' by default.
    """
    run_dir = get_audit_run_dir(audit_run_id, workspace_root)
    state_file = os.path.join(run_dir, "suggestion_state.json")
    
    if os.path.exists(state_file):
        with open(state_file, "r", encoding="utf-8") as f:
            return json.load(f)
            
    # Initializing from existing findings files in the run directory
    classified_file = os.path.join(run_dir, "classified_findings.json")
    report_file = os.path.join(run_dir, "audit_report.json")
    
    findings = []
    if os.path.exists(classified_file):
        with open(classified_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            findings = data.get("findings", [])
    elif os.path.exists(report_file):
        with open(report_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            findings = data.get("findings", [])
            
    states = {}
    for f in findings:
        fid = f.get("finding_id") if isinstance(f, dict) else getattr(f, "finding_id", None)
        if fid:
            states[fid] = "NEW"
            
    if states:
        os.makedirs(run_dir, exist_ok=True)
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(states, f, indent=2, ensure_ascii=False)
            
    return states

def update_suggestion_state(audit_run_id: str, suggestion_id: str, to_status: str, workspace_root: Optional[str] = None) -> None:
    """
    Updates suggestion_state.json by transitioning the specified suggestion_id to to_status.
    """
    run_dir = get_audit_run_dir(audit_run_id, workspace_root)
    state_file = os.path.join(run_dir, "suggestion_state.json")
    
    states = load_suggestion_states(audit_run_id, workspace_root)
    states[suggestion_id] = to_status
    
    os.makedirs(run_dir, exist_ok=True)
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(states, f, indent=2, ensure_ascii=False)

def record_action_log(audit_run_id: str, log: SuggestionActionLog, workspace_root: Optional[str] = None) -> None:
    """
    Appends the action log into the suggestion_actions.jsonl file inside the audit run folder.
    """
    run_dir = get_audit_run_dir(audit_run_id, workspace_root)
    actions_file = os.path.join(run_dir, "suggestion_actions.jsonl")
    
    os.makedirs(run_dir, exist_ok=True)
    with open(actions_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(log.model_dump(), ensure_ascii=False) + "\n")

def get_action_logs(audit_run_id: str, workspace_root: Optional[str] = None) -> List[dict]:
    """
    Returns the complete action log history from suggestion_actions.jsonl.
    """
    run_dir = get_audit_run_dir(audit_run_id, workspace_root)
    actions_file = os.path.join(run_dir, "suggestion_actions.jsonl")
    
    if not os.path.exists(actions_file):
        return []
        
    logs = []
    with open(actions_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                logs.append(json.loads(line))
    return logs
