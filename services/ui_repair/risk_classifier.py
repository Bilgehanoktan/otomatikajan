import enum
from typing import Dict, Any, List

class FailureType(str, enum.Enum):
    BLANK_PAGE = "BLANK_PAGE"
    ROUTE_404 = "ROUTE_404"
    API_404 = "API_404"
    API_500 = "API_500"
    CONSOLE_ERROR = "CONSOLE_ERROR"
    HYDRATION_ERROR = "HYDRATION_ERROR"
    REDIRECT_LOOP = "REDIRECT_LOOP"
    NETWORK_FAILURE = "NETWORK_FAILURE"
    LAYOUT_COLLAPSE = "LAYOUT_COLLAPSE"
    TIMEOUT = "TIMEOUT"
    UNKNOWN = "UNKNOWN"

class UIRiskClassifier:
    """Classifies UI failures and determines their impact/severity."""
    
    CRITICAL_ROUTES = [
        "/governance", 
        "/approvals", 
        "/audit", 
        "/workflows", 
        "/system-health",
        "/repair-lab",
        "/dashboard"
    ]

    @classmethod
    def classify(cls, evidence: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classifies the failure type and determines severity.
        
        Rules:
        - Critical routes (auth, gov, health) have escalated severity.
        - Blank pages on critical routes are HIGH/CRITICAL.
        - Hydration errors are typically MEDIUM.
        - Console errors with Type/Reference errors are MEDIUM/HIGH.
        """
        route = evidence.get("route", "")
        http_status = evidence.get("http_status", 0)
        blank_page = evidence.get("blank_page_detected", False)
        console_errors = evidence.get("console_errors", [])
        network_errors = evidence.get("network_errors", [])
        error_detail = evidence.get("error_detail", "")
        
        failure_type = FailureType.UNKNOWN
        severity = "LOW"
        
        # 1. Determine failure type
        if http_status == 404:
            failure_type = FailureType.ROUTE_404
        elif http_status >= 500:
            failure_type = FailureType.API_500
        elif blank_page:
            failure_type = FailureType.BLANK_PAGE
        elif any("hydration" in str(err).lower() for err in console_errors):
            failure_type = FailureType.HYDRATION_ERROR
        elif console_errors:
            failure_type = FailureType.CONSOLE_ERROR
        elif network_errors:
            if any(str(n.get("status")) == "404" for n in network_errors):
                failure_type = FailureType.API_404
            elif any(str(n.get("status")) == "500" for n in network_errors):
                failure_type = FailureType.API_500
            else:
                failure_type = FailureType.NETWORK_FAILURE
        elif "timeout" in error_detail.lower():
            failure_type = FailureType.TIMEOUT
                
        # 2. Determine severity
        is_critical_route = any(route.startswith(cr) for cr in cls.CRITICAL_ROUTES) or route == "/"
        
        if failure_type in [FailureType.ROUTE_404, FailureType.BLANK_PAGE, FailureType.API_500, FailureType.TIMEOUT]:
            severity = "HIGH" if is_critical_route else "MEDIUM"
        elif failure_type == FailureType.HYDRATION_ERROR:
            severity = "MEDIUM"
        elif failure_type == FailureType.CONSOLE_ERROR:
            # Check for critical console errors
            critical_keywords = ["TypeError", "ReferenceError", "Cannot read properties", "is not a function", "failed to fetch"]
            error_strings = [str(err.get("text", "")).lower() for err in console_errors]
            if any(any(kw.lower() in es for kw in critical_keywords) for es in error_strings):
                severity = "HIGH" if is_critical_route else "MEDIUM"
            else:
                severity = "LOW"
        
        # Redirect loop detection (often manifests as too many redirects or timeout)
        if "redirect" in error_detail.lower() or "too many" in error_detail.lower():
            failure_type = FailureType.REDIRECT_LOOP
            severity = "CRITICAL"

        return {
            "failure_type": failure_type.value,
            "severity": severity
        }
