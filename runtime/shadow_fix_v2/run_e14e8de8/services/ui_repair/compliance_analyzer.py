import re
from typing import List, Dict, Any, Tuple

class ComplianceAnalyzer:
    """Checks repair patches for compliance with security and privacy standards."""
    
    # Simple patterns for demonstration
    PII_PATTERNS = [
        (re.compile(r'email|password|credit_card|ssn|phone', re.I), "Potential PII leaked in logs/UI"),
        (re.compile(r'eval\(|exec\(', re.I), "Unsafe execution pattern detected"),
        (re.compile(r'http://', re.I), "Non-secure protocol used (HTTPS required)")
    ]

    @staticmethod
    def analyze_patch(patch_content: str) -> List[Dict[str, Any]]:
        """Analyzes a git patch for compliance violations."""
        findings = []
        
        # Split patch into additions
        additions = [line[1:] for line in patch_content.splitlines() if line.startswith('+')]
        
        for line in additions:
            for pattern, reason in ComplianceAnalyzer.PII_PATTERNS:
                if pattern.search(line):
                    findings.append({
                        "type": "COMPLIANCE_VIOLATION",
                        "severity": "CRITICAL",
                        "reason": reason,
                        "line": line.strip()
                    })
        
        return findings

    @staticmethod
    def check_gdpr_compliance(context: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Checks if the operation context respects GDPR (e.g., data residency)."""
        violations = []
        region = context.get("target_region", "EU")
        data_handling = context.get("handles_user_data", False)
        
        if region == "EU" and not context.get("consent_verified", False) and data_handling:
            violations.append("User data processed in EU without verified consent")
            
        return len(violations) == 0, violations
