import os
import json
from typing import Dict, Any, Optional
from services.self_repair_audit.suggestion_store import get_audit_run_dir

def load_suggestion_run_links(audit_run_id: str, workspace_root: Optional[str] = None) -> Dict[str, Any]:
    """
    Loads suggestion run links from suggestion_run_links.json.
    If the file does not exist, returns an empty dictionary.
    """
    run_dir = get_audit_run_dir(audit_run_id, workspace_root)
    links_file = os.path.join(run_dir, "suggestion_run_links.json")
    
    if os.path.exists(links_file):
        try:
            with open(links_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_suggestion_run_link(
    audit_run_id: str,
    suggestion_id: str,
    run_data: Dict[str, Any],
    workspace_root: Optional[str] = None
) -> None:
    """
    Saves a run link association for a suggestion to suggestion_run_links.json.
    """
    run_dir = get_audit_run_dir(audit_run_id, workspace_root)
    links_file = os.path.join(run_dir, "suggestion_run_links.json")
    
    links = load_suggestion_run_links(audit_run_id, workspace_root)
    links[suggestion_id] = run_data
    
    os.makedirs(run_dir, exist_ok=True)
    with open(links_file, "w", encoding="utf-8") as f:
        json.dump(links, f, indent=2, ensure_ascii=False)
