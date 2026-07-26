import fnmatch
from typing import List, Dict, Any, Optional, Tuple


class RiskEngine:
    """
    Risk Assessment Engine for BilgeAPI Governance.
    Evaluates risk levels for file paths, commands, and operations.
    """

    CRITICAL_PATTERNS = [
        "**/.env*", "**/database/*.db", "**/.git/**/*", "**/.bilgeapi/**/*", "**/auth_models.py"
    ]
    HIGH_PATTERNS = [
        "**/settings.py", "**/package.json", "**/auth/*", "**/security/*", "**/login.py"
    ]

    def __init__(self, risk_rules: Optional[List[Dict[str, Any]]] = None):
        self.risk_rules = risk_rules or []

    def evaluate_path(self, target_path: str) -> Tuple[str, float, str]:
        path_str = str(target_path).replace("\\", "/")

        for pattern in self.CRITICAL_PATTERNS:
            if fnmatch.fnmatch(path_str, pattern) or fnmatch.fnmatch(f"/{path_str}", pattern) or pattern.replace("**/", "") in path_str:
                return "CRITICAL", 10.0, f"Target '{target_path}' matches critical security policy pattern"

        for pattern in self.HIGH_PATTERNS:
            if fnmatch.fnmatch(path_str, pattern) or fnmatch.fnmatch(f"/{path_str}", pattern) or pattern.replace("**/", "") in path_str:
                return "HIGH", 8.0, f"Target '{target_path}' matches high risk policy pattern"

        if "src/" in path_str or "apps/" in path_str:
            return "MEDIUM", 5.0, f"Target '{target_path}' is standard application code"

        return "LOW", 1.0, f"Target '{target_path}' is low risk"
