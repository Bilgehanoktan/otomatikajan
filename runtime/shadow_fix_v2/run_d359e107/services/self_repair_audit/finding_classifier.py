from typing import List, Dict, Any
from services.self_repair_audit.models import Finding

def calculate_priority_score(severity: str, category: str) -> int:
    """
    Determines an integer priority score (0-100) based on severity and category importance.
    """
    severity_base = {
        "CRITICAL": 95,
        "HIGH": 80,
        "MEDIUM": 50,
        "LOW": 20,
        "INFO": 5
    }
    
    category_modifier = {
        "security": 4,
        "api_contract": 3,
        "test_build": 2,
        "project_factory": 1,
        "dashboard_health": 0
    }
    
    base = severity_base.get(severity.upper(), 5)
    mod = category_modifier.get(category.lower(), 0)
    
    score = base + mod
    return min(100, max(0, score))

def classify_and_score_finding(finding: Finding) -> Finding:
    """
    Classifies a single finding, ensuring it has an appropriate priority score and category-specific safety locks.
    """
    finding.severity = finding.severity.upper()
    if finding.severity not in {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"}:
        finding.severity = "MEDIUM"
        
    finding.priority_score = calculate_priority_score(finding.severity, finding.category)
    
    # Security rule check
    if finding.category == "security":
        finding.requires_human_approval = True
        
    return finding

def classify_findings(findings: List[Finding]) -> List[Finding]:
    """
    Processes and scores a list of findings sequentially.
    """
    processed = []
    for idx, f in enumerate(findings):
        # Format finding ID if not already structured
        if not f.finding_id or f.finding_id == "...":
            f.finding_id = f"AUD-FIND-{idx+1:03d}"
        
        processed.append(classify_and_score_finding(f))
    return processed
