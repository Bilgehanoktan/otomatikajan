import os
import json
import re
from typing import Any, Dict

def scrub_sensitive_data(data: Any) -> Any:
    """
    Recursively scrubs secrets, tokens, api keys, and passwords from dictionary, lists, or strings.
    """
    sensitive_keys = {
        "token", "password", "secret", "apikey", "api_key", "auth", "credential", 
        "private_key", "session_id", "access_key", "db_url", "database_url"
    }

    if isinstance(data, dict):
        scrubbed = {}
        for k, v in data.items():
            k_lower = k.lower()
            if any(sk in k_lower for sk in sensitive_keys):
                scrubbed[k] = "[SCRUBBED]"
            else:
                scrubbed[k] = scrub_sensitive_data(v)
        return scrubbed
    elif isinstance(data, list):
        return [scrub_sensitive_data(item) for item in data]
    elif isinstance(data, str):
        # Scrub common authorization headers or token assignments if they appear in strings
        # e.g., "Bearer 12345" or "secret=foo"
        data = re.sub(r'(bearer\s+)[a-zA-Z0-9_\-\.]+', r'\1[SCRUBBED]', data, flags=re.IGNORECASE)
        data = re.sub(r'(secret|password|token|apikey|api_key)\s*=\s*[a-zA-Z0-9_\-\.\'\"]+', r'\1=[SCRUBBED]', data, flags=re.IGNORECASE)
        return data
    return data

def save_artifact(audit_run_id: str, filename: str, artifact_data: Any, workspace_root: str = None) -> str:
    """
    Scrubs and saves the artifact JSON inside project_outputs/audit_runs/{audit_run_id}/filename.
    """
    scrubbed_data = scrub_sensitive_data(artifact_data)
    
    if not workspace_root:
        workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    output_dir = os.path.join(workspace_root, "project_outputs", "audit_runs", audit_run_id)
    os.makedirs(output_dir, exist_ok=True)
    
    file_path = os.path.join(output_dir, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(scrubbed_data, f, indent=2, ensure_ascii=False)
        
    return file_path

