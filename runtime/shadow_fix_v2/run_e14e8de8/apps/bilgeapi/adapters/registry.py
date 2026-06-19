import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone

from apps.bilgeapi.config import settings
from apps.bilgeapi.adapters.interface import ExternalAdapter
from apps.bilgeapi.adapters.github_issue import GitHubIssueAdapter
from apps.bilgeapi.adapters.jira import JiraAdapter
from apps.bilgeapi.adapters.sovereign_repair_lab import SovereignRepairLabAdapter
from apps.bilgeapi.adapters.webhook import WebhookDispatcher, is_ssrf_safe
from apps.bilgeapi.adapters.slack_teams import SlackAdapter, TeamsAdapter

logger = logging.getLogger("bilgeapi.adapter_registry")

class WebhookAdapter(ExternalAdapter):
    def __init__(self, dispatcher: Optional[WebhookDispatcher] = None):
        self.dispatcher = dispatcher or WebhookDispatcher()

    @property
    def name(self) -> str:
        return "webhook"

    @property
    def enabled(self) -> bool:
        return True

    @property
    def configured(self) -> bool:
        return bool(settings.BILGEAPI_WEBHOOK_URL)

    async def health_check(self) -> str:
        if not self.configured:
            return "not_configured"
        url = settings.BILGEAPI_WEBHOOK_URL
        allow_private = settings.BILGEAPI_ALLOW_PRIVATE_WEBHOOKS
        if not is_ssrf_safe(url, allow_private=allow_private):
            return "unhealthy"
        return "healthy"

    async def dispatch(self, repair_request_id: str, payload: dict, dry_run: bool = False, webhook_url: Optional[str] = None, dispatcher: Optional[WebhookDispatcher] = None) -> dict:
        url = webhook_url or settings.BILGEAPI_WEBHOOK_URL
        if not url:
            return {"status": "FAILED", "error_message": "Webhook URL is not configured."}

        allow_private = settings.BILGEAPI_ALLOW_PRIVATE_WEBHOOKS
        if not is_ssrf_safe(url, allow_private=allow_private):
            return {"status": "FAILED", "error_message": f"SSRF Guard: URL {url} is forbidden."}

        if dry_run:
            logger.info(f"[Dry-run] Webhook simulation successful for {repair_request_id}")
            return {
                "status": "SENT",
                "external_reference": "webhook:dry-run",
                "raw_response": {"status": "mocked"}
            }

        idempotency_key = f"idemp_{repair_request_id}"
        timestamp = datetime.now(timezone.utc).isoformat()
        secret = settings.BILGEAPI_WEBHOOK_SECRET

        disp = dispatcher or self.dispatcher
        try:
            response = await disp.dispatch(
                url=url,
                payload=payload,
                signature_secret=secret,
                idempotency_key=idempotency_key,
                timestamp=timestamp
            )
            status_code = response.status_code
            if 200 <= status_code < 300:
                ref = f"webhook:web_{repair_request_id}"
                if len(ref) > 64:
                    ref = ref[:64]
                return {
                    "status": "SENT",
                    "external_reference": ref,
                    "raw_response": {"status_code": status_code}
                }
            else:
                return {
                    "status": "FAILED",
                    "error_message": f"Webhook returned status code: {status_code}"
                }
        except Exception as e:
            raise e


class AdapterRegistry:
    def __init__(self, dispatcher: Optional[WebhookDispatcher] = None):
        self._adapters: Dict[str, ExternalAdapter] = {
            "webhook": WebhookAdapter(dispatcher),
            "github_issue": GitHubIssueAdapter(),
            "jira": JiraAdapter(),
            "sovereign_repair_lab": SovereignRepairLabAdapter(),
            "slack": SlackAdapter(),
            "teams": TeamsAdapter()
        }

    def get_adapter(self, name: str) -> Optional[ExternalAdapter]:
        return self._adapters.get(name)

    def list_adapters(self) -> List[ExternalAdapter]:
        return list(self._adapters.values())

# Global registry instance
adapter_registry = AdapterRegistry()
