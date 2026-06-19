import re
import logging
from typing import List, Dict, Any
from uuid import UUID

logger = logging.getLogger(__name__)

class ComplianceGuardrails:
    """
    Scans autonomous artifacts (patches, reports, logs) for compliance violations.
    """

    SECRET_PATTERNS = [
        r"(?i)api_key[\s:=]+['\"]?([a-z0-9-]{24,})['\"]?",
        r"(?i)secret[\s:=]+['\"]?([a-z0-9/+=]{32,})['\"]?",
        r"(?i)bearer\s+[a-z0-9._~+/-]+",
        r"(?i)password[\s:=]+['\"]?[^'\"]{8,}['\"]?",
        r"sk-[a-zA-Z0-9]{20,}", # OpenAI style
    ]

    def __init__(self, project_key: str):
        self.project_key = project_key

    def scan_patch(self, patch_content: str) -> List[Dict[str, Any]]:
        """Scans a git patch for secrets or unsafe patterns."""
        findings = []

        # 1. Secret/Token Exposure Check
        for pattern in self.SECRET_PATTERNS:
            matches = re.finditer(pattern, patch_content)
            for match in matches:
                findings.append({
                    "standard": "INTERNAL_SECURITY",
                    "severity": "CRITICAL",
                    "finding_type": "SECRET_EXPOSURE",
                    "description": f"Potential secret detected in patch: {match.group(0)[:10]}...",
                    "recommendation": "Remove hardcoded secrets and use environment variables."
                })

        # 2. Audit/Evidence Hook Removal Check
        if "DecisionLineage" in patch_content and "-" in patch_content:
             findings.append({
                "standard": "AUDIT_RETENTION",
                "severity": "HIGH",
                "finding_type": "AUDIT_BYPASS",
                "description": "Attempt to remove or modify audit logging hooks detected.",
                "recommendation": "Do not modify the DecisionLineage integration."
            })

        # 3. Auth/Session Risk
        if any(keyword in patch_content.lower() for keyword in ["session", "cookie", "auth", "token_storage"]):
            findings.append({
                "standard": "ACCESS_CONTROL",
                "severity": "MEDIUM",
                "finding_type": "AUTH_SENSITIVE_CHANGE",
                "description": "Modifications to authentication or session handling detected.",
                "recommendation": "Manual review required for security-sensitive areas."
            })

        return findings

    def scan_report(self, report_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scans diagnostic reports for PII or sensitive leakage."""
        findings = []
        report_str = str(report_data)

        # Basic PII detection (emails, phones - simple examples)
        email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
        if re.search(email_pattern, report_str):
            findings.append({
                "standard": "GDPR_LIKE",
                "severity": "HIGH",
                "finding_type": "PII_LEAKAGE",
                "description": "Unmasked email addresses detected in diagnostic report.",
                "recommendation": "Ensure all PII is masked before storage."
            })

        return findings
