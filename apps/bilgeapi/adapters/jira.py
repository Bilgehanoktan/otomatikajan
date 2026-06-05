import logging
import base64
from typing import Optional
import httpx
from apps.bilgeapi.config import settings
from apps.bilgeapi.adapters.interface import ExternalAdapter

logger = logging.getLogger("bilgeapi.jira_adapter")

class JiraAdapter(ExternalAdapter):
    @property
    def name(self) -> str:
        return "jira"

    @property
    def enabled(self) -> bool:
        return settings.BILGEAPI_JIRA_ENABLED

    @property
    def configured(self) -> bool:
        return bool(
            settings.BILGEAPI_JIRA_BASE_URL and
            settings.BILGEAPI_JIRA_EMAIL and
            settings.BILGEAPI_JIRA_API_TOKEN
        )

    def _get_auth_header(self) -> str:
        email = settings.BILGEAPI_JIRA_EMAIL or ""
        token = settings.BILGEAPI_JIRA_API_TOKEN or ""
        auth_str = f"{email}:{token}"
        encoded = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
        return f"Basic {encoded}"

    async def health_check(self) -> str:
        if not self.enabled:
            return "disabled"
        if not self.configured:
            return "not_configured"
        
        # Test API using a light GET /rest/api/2/myself to verify credentials
        url = f"{settings.BILGEAPI_JIRA_BASE_URL.rstrip('/')}/rest/api/2/myself"
        headers = {
            "Authorization": self._get_auth_header(),
            "Accept": "application/json",
            "User-Agent": "BilgeAPI"
        }
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                return "healthy"
            else:
                logger.warning(f"Jira health check failed with status: {resp.status_code}")
                return "unhealthy"
        except Exception as e:
            logger.warning(f"Jira health check failed: {e}")
            return "unhealthy"

    async def dispatch(self, repair_request_id: str, payload: dict, dry_run: bool = False) -> dict:
        if not self.enabled:
            return {"status": "FAILED", "error_message": "Jira Adapter is disabled."}
        if not self.configured:
            return {"status": "FAILED", "error_message": "Jira Adapter is not fully configured."}

        repair_req = payload.get("repair_request", {})
        incident = payload.get("incident") or {}
        diagnostic = payload.get("diagnostic") or {}

        severity = incident.get("severity", "MEDIUM")
        source = incident.get("source_system", "unknown")
        project_key = incident.get("project_key", "unknown")
        err_msg = incident.get("error_message", "No error message provided")

        summary = f"[BilgeAPI][{severity}][{project_key}] {err_msg}"
        if len(summary) > 250:
            summary = summary[:247] + "..."

        description = f"""Incident Summary:
- Project: {project_key}
- Source: {source}
- Environment: {incident.get("environment", "unknown")}
- Severity: {severity}
- Error Message: {err_msg}

Diagnostic Analysis:
- Root Cause Hypothesis: {diagnostic.get("root_cause_hypothesis", "No hypothesis provided")}
- Confidence: {diagnostic.get("confidence", "n/a")}

Risk scoring:
- Risk Score: {repair_req.get("risk_score", "n/a")}
- Risk Reason: {repair_req.get("risk_reason", "No reason provided")}

Governance Details:
- Approval Required: {str(repair_req.get("approval_required", True)).lower()}
- Approved By: {repair_req.get("approved_by") or "n/a"}
- Repair Request ID: {repair_request_id}
"""

        if dry_run:
            logger.info(f"[Dry-run] Jira ticket creation simulation successful for {repair_request_id}")
            return {
                "status": "SENT",
                "external_reference": "jira:OPS-123",
                "raw_response": {"key": "OPS-123", "id": "10001", "self": "https://jira/dry-run"}
            }

        url = f"{settings.BILGEAPI_JIRA_BASE_URL.rstrip('/')}/rest/api/2/issue"
        headers = {
            "Authorization": self._get_auth_header(),
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "BilgeAPI"
        }

        body_data = {
            "fields": {
                "project": {
                    "key": settings.BILGEAPI_JIRA_PROJECT_KEY
                },
                "summary": summary,
                "description": description,
                "issuetype": {
                    "name": settings.BILGEAPI_JIRA_ISSUE_TYPE
                },
                "labels": ["bilgeapi", "repair-request"]
            }
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=body_data, headers=headers)
            
            if 200 <= resp.status_code < 300:
                resp_json = resp.json()
                key = resp_json.get("key", "n/a")
                ref = f"jira:{key}"
                if len(ref) > 64:
                    ref = ref[:64]
                return {
                    "status": "SENT",
                    "external_reference": ref,
                    "raw_response": resp_json
                }
            else:
                return {
                    "status": "FAILED",
                    "error_message": f"Jira returned status code: {resp.status_code}. Response: {resp.text}"
                }
        except Exception as e:
            return {
                "status": "FAILED",
                "error_message": f"Jira dispatch exception: {str(e)}"
            }
