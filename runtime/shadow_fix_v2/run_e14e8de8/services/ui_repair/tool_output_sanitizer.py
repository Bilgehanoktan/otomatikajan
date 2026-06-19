import hashlib
from typing import Any, Dict, Tuple
from services.ui_repair.tool_secret_guard import ToolSecretGuard

class ToolOutputSanitizer:
    def __init__(self):
        self.secret_guard = ToolSecretGuard()

    def sanitize_output(self, output: Any) -> Tuple[Any, bool]:
        """Sanitizes tool output and returns (clean_data, redaction_occurred)."""
        return self.secret_guard.sanitize_data(output)

    def hash_evidence(self, data: Any) -> str:
        """Generates a stable hash for the sanitized evidence."""
        # Convert to stable string representation for hashing
        if isinstance(data, (dict, list)):
            import json
            data_str = json.dumps(data, sort_keys=True, default=str)
        else:
            data_str = str(data)
        
        return hashlib.sha256(data_str.encode()).hexdigest()
