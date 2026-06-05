import logging
import httpx
from typing import Optional
from apps.bilgeapi.config import settings
from apps.bilgeapi.adapters.interface import ExternalAdapter
from apps.bilgeapi.adapters.webhook import is_ssrf_safe

logger = logging.getLogger("bilgeapi.slack_teams")

class SlackMessageFormatter:
    def format_message(self, repair_request_id: str, payload: dict) -> dict:
        """
        Formats the Slack payload. In this initial version, it generates a markdown-compatible
        text layout. Can be subclassed or updated to use Slack Block Kit.
        """
        incident = payload.get("incident", {})
        diag = payload.get("diagnostic", {})
        
        text = (
            f"📡 *[BilgeAPI] Repair Request Dispatched*\n"
            f"• *Request ID:* `{repair_request_id}`\n"
            f"• *Incident Kind:* `{incident.get('kind', 'N/A')}`\n"
            f"• *Severity:* `{incident.get('severity', 'N/A')}`\n"
            f"• *Error Message:* `{incident.get('error_message', 'N/A')}`\n"
            f"• *Diagnostic Summary:* {diag.get('summary', 'N/A')}\n"
            f"• *Root Cause Hypothesis:* {diag.get('root_cause_hypothesis', 'N/A')}\n"
            f"• *Confidence:* `{diag.get('confidence', 'N/A')}`"
        )
        return {"text": text}

class TeamsMessageFormatter:
    def format_message(self, repair_request_id: str, payload: dict) -> dict:
        """
        Formats the Teams payload. In this initial version, it generates a markdown-compatible
        text layout. Can be subclassed or updated to use Teams Adaptive Cards.
        """
        incident = payload.get("incident", {})
        diag = payload.get("diagnostic", {})
        
        text = (
            f"## 📡 [BilgeAPI] Repair Request Dispatched\n"
            f"- **Request ID:** `{repair_request_id}`\n"
            f"- **Incident Kind:** `{incident.get('kind', 'N/A')}`\n"
            f"- **Severity:** `{incident.get('severity', 'N/A')}`\n"
            f"- **Error Message:** `{incident.get('error_message', 'N/A')}`\n"
            f"- **Diagnostic Summary:** {diag.get('summary', 'N/A')}\n"
            f"- **Root Cause Hypothesis:** {diag.get('root_cause_hypothesis', 'N/A')}\n"
            f"- **Confidence:** `{diag.get('confidence', 'N/A')}`"
        )
        return {"text": text}

class SlackAdapter(ExternalAdapter):
    def __init__(self, formatter: Optional[SlackMessageFormatter] = None):
        self.formatter = formatter or SlackMessageFormatter()

    @property
    def name(self) -> str:
        return "slack"

    @property
    def enabled(self) -> bool:
        return True

    @property
    def configured(self) -> bool:
        return bool(settings.BILGEAPI_SLACK_WEBHOOK_URL)

    async def health_check(self) -> str:
        if not self.configured:
            return "not_configured"
        url = settings.BILGEAPI_SLACK_WEBHOOK_URL
        allow_private = settings.BILGEAPI_ALLOW_PRIVATE_WEBHOOKS
        if not is_ssrf_safe(url, allow_private=allow_private):
            return "unhealthy"
        return "healthy"

    async def dispatch(self, repair_request_id: str, payload: dict, dry_run: bool = False) -> dict:
        url = settings.BILGEAPI_SLACK_WEBHOOK_URL
        if not url:
            return {"status": "FAILED", "error_message": "Slack Webhook URL is not configured."}

        allow_private = settings.BILGEAPI_ALLOW_PRIVATE_WEBHOOKS
        if not is_ssrf_safe(url, allow_private=allow_private):
            return {"status": "FAILED", "error_message": f"SSRF Guard: URL {url} is forbidden."}

        slack_body = self.formatter.format_message(repair_request_id, payload)

        if dry_run:
            logger.info(f"[Dry-run] Slack notification simulation successful for {repair_request_id}")
            return {
                "status": "SENT",
                "external_reference": "slack:dry-run",
                "raw_response": {"status": "mocked"}
            }

        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=False) as client:
                response = await client.post(url, json=slack_body)
                if 200 <= response.status_code < 300:
                    return {
                        "status": "SENT",
                        "external_reference": f"slack:msg_{repair_request_id[:20]}",
                        "raw_response": {"status_code": response.status_code}
                    }
                else:
                    return {
                        "status": "FAILED",
                        "error_message": f"Slack webhook returned status code: {response.status_code}"
                    }
        except Exception as e:
            return {
                "status": "FAILED",
                "error_message": f"Failed to send Slack webhook: {str(e)}"
            }

class TeamsAdapter(ExternalAdapter):
    def __init__(self, formatter: Optional[TeamsMessageFormatter] = None):
        self.formatter = formatter or TeamsMessageFormatter()

    @property
    def name(self) -> str:
        return "teams"

    @property
    def enabled(self) -> bool:
        return True

    @property
    def configured(self) -> bool:
        return bool(settings.BILGEAPI_TEAMS_WEBHOOK_URL)

    async def health_check(self) -> str:
        if not self.configured:
            return "not_configured"
        url = settings.BILGEAPI_TEAMS_WEBHOOK_URL
        allow_private = settings.BILGEAPI_ALLOW_PRIVATE_WEBHOOKS
        if not is_ssrf_safe(url, allow_private=allow_private):
            return "unhealthy"
        return "healthy"

    async def dispatch(self, repair_request_id: str, payload: dict, dry_run: bool = False) -> dict:
        url = settings.BILGEAPI_TEAMS_WEBHOOK_URL
        if not url:
            return {"status": "FAILED", "error_message": "Teams Webhook URL is not configured."}

        allow_private = settings.BILGEAPI_ALLOW_PRIVATE_WEBHOOKS
        if not is_ssrf_safe(url, allow_private=allow_private):
            return {"status": "FAILED", "error_message": f"SSRF Guard: URL {url} is forbidden."}

        teams_body = self.formatter.format_message(repair_request_id, payload)

        if dry_run:
            logger.info(f"[Dry-run] Teams notification simulation successful for {repair_request_id}")
            return {
                "status": "SENT",
                "external_reference": "teams:dry-run",
                "raw_response": {"status": "mocked"}
            }

        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=False) as client:
                response = await client.post(url, json=teams_body)
                if 200 <= response.status_code < 300:
                    return {
                        "status": "SENT",
                        "external_reference": f"teams:msg_{repair_request_id[:20]}",
                        "raw_response": {"status_code": response.status_code}
                    }
                else:
                    return {
                        "status": "FAILED",
                        "error_message": f"Teams webhook returned status code: {response.status_code}"
                    }
        except Exception as e:
            return {
                "status": "FAILED",
                "error_message": f"Failed to send Teams webhook: {str(e)}"
            }
