import logging
from typing import Optional
import httpx
from apps.bilgeapi.config import settings
from apps.bilgeapi.adapters.interface import ExternalAdapter

logger = logging.getLogger("bilgeapi.github_adapter")

class GitHubIssueAdapter(ExternalAdapter):
    @property
    def name(self) -> str:
        return "github_issue"

    @property
    def enabled(self) -> bool:
        return settings.BILGEAPI_GITHUB_ENABLED

    @property
    def configured(self) -> bool:
        return bool(
            settings.BILGEAPI_GITHUB_TOKEN and
            settings.BILGEAPI_GITHUB_OWNER and
            settings.BILGEAPI_GITHUB_REPO
        )

    async def health_check(self) -> str:
        if not self.enabled:
            return "disabled"
        if not self.configured:
            return "not_configured"
        
        url = f"https://api.github.com/repos/{settings.BILGEAPI_GITHUB_OWNER}/{settings.BILGEAPI_GITHUB_REPO}"
        headers = {
            "Authorization": f"Bearer {settings.BILGEAPI_GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "BilgeAPI"
        }
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                return "healthy"
            else:
                logger.warning(f"GitHub health check failed with status: {resp.status_code}")
                return "unhealthy"
        except Exception as e:
            logger.warning(f"GitHub health check failed: {e}")
            return "unhealthy"

    async def dispatch(self, repair_request_id: str, payload: dict, dry_run: bool = False) -> dict:
        if not self.enabled:
            return {"status": "FAILED", "error_message": "GitHub Adapter is disabled."}
        if not self.configured:
            return {"status": "FAILED", "error_message": "GitHub Adapter is not fully configured."}

        repair_req = payload.get("repair_request", {})
        incident = payload.get("incident") or {}
        diagnostic = payload.get("diagnostic") or {}

        severity = incident.get("severity", "MEDIUM")
        source = incident.get("source_system", "unknown")
        project = incident.get("project_key", "unknown")
        err_msg = incident.get("error_message", "No error message provided")

        title = f"[BilgeAPI][{severity}][{project}] {err_msg}"
        if len(title) > 120:
            title = title[:117] + "..."

        body = f"""## Incident Summary

Project: {project}  
Source: {source}  
Environment: {incident.get("environment", "unknown")}  
Severity: {severity}  
Error Message: {err_msg}  

## Diagnostic

Root Cause Hypothesis:
{diagnostic.get("root_cause_hypothesis", "No hypothesis provided")}

Confidence:
{diagnostic.get("confidence", "n/a")}

## Risk

Risk Score:
{repair_req.get("risk_score", "n/a")}

Risk Reason:
{repair_req.get("risk_reason", "No reason provided")}

## Governance

Approval Required: {str(repair_req.get("approval_required", True)).lower()}  
Approved By: {repair_req.get("approved_by") or "n/a"}  
Dispatch Status: DISPATCHED  
Repair Request ID: {repair_request_id}  
"""

        labels_str = settings.BILGEAPI_GITHUB_LABELS
        labels = [l.strip() for l in labels_str.split(",") if l.strip()]

        if dry_run:
            logger.info(f"[Dry-run] GitHub issue simulation successful for {repair_request_id}")
            return {
                "status": "SENT",
                "external_reference": f"github:dry-run-42",
                "raw_response": {"number": 42, "url": "https://github.com/dry-run"}
            }

        url = f"https://api.github.com/repos/{settings.BILGEAPI_GITHUB_OWNER}/{settings.BILGEAPI_GITHUB_REPO}/issues"
        headers = {
            "Authorization": f"Bearer {settings.BILGEAPI_GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "BilgeAPI"
        }
        body_data = {
            "title": title,
            "body": body,
            "labels": labels
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=body_data, headers=headers)
            
            if 200 <= resp.status_code < 300:
                resp_json = resp.json()
                issue_num = resp_json.get("number")
                # Ensure the external reference is strictly under 64 characters
                ref = f"github:{settings.BILGEAPI_GITHUB_OWNER}/{settings.BILGEAPI_GITHUB_REPO}#{issue_num}"
                if len(ref) > 64:
                    ref = f"github:issue#{issue_num}"
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
                    "error_message": f"GitHub returned status code: {resp.status_code}. Response: {resp.text}"
                }
        except Exception as e:
            return {
                "status": "FAILED",
                "error_message": f"GitHub dispatch exception: {str(e)}"
            }
