import logging
from typing import Optional
import httpx
from apps.bilgeapi.config import settings
from apps.bilgeapi.adapters.interface import ExternalAdapter

logger = logging.getLogger("bilgeapi.sovereign_adapter")

class SovereignRepairLabAdapter(ExternalAdapter):
    @property
    def name(self) -> str:
        return "sovereign_repair_lab"

    @property
    def enabled(self) -> bool:
        return settings.BILGEAPI_SOVEREIGN_ENABLED

    @property
    def configured(self) -> bool:
        return bool(
            settings.BILGEAPI_SOVEREIGN_BASE_URL and
            settings.BILGEAPI_SOVEREIGN_API_KEY
        )

    async def health_check(self) -> str:
        if not self.enabled:
            return "disabled"
        if not self.configured:
            return "not_configured"
        
        # Test connectivity using a light GET /health
        url = f"{settings.BILGEAPI_SOVEREIGN_BASE_URL.rstrip('/')}/health"
        headers = {
            "X-API-Key": settings.BILGEAPI_SOVEREIGN_API_KEY,
            "Accept": "application/json",
            "User-Agent": "BilgeAPI"
        }
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url, headers=headers)
            # Accept 200, 404 (if /health does not exist but server responded), or any non-timeout/connection error
            if resp.status_code < 500:
                return "healthy"
            else:
                logger.warning(f"Sovereign health check failed with status: {resp.status_code}")
                return "unhealthy"
        except Exception as e:
            logger.warning(f"Sovereign health check failed: {e}")
            return "unhealthy"

    async def dispatch(self, repair_request_id: str, payload: dict, dry_run: bool = False) -> dict:
        if not self.enabled:
            return {"status": "FAILED", "error_message": "Sovereign Adapter is disabled."}
        if not self.configured:
            return {"status": "FAILED", "error_message": "Sovereign Adapter is not fully configured."}

        repair_req = payload.get("repair_request", {})
        incident = payload.get("incident") or {}
        diagnostic = payload.get("diagnostic") or {}

        recommendations = diagnostic.get("recommendations", [])
        project_key = incident.get("project_key", "unknown")
        environment = incident.get("environment", "unknown")

        body_data = {
            "source": "bilgeapi",
            "incident_id": incident.get("id"),
            "diagnostic_id": repair_req.get("diagnostic_id"),
            "repair_request_id": repair_request_id,
            "risk_score": repair_req.get("risk_score"),
            "approval_status": str(repair_req.get("approval_status")),
            "recommendations": recommendations,
            "metadata": {
                "project_key": project_key,
                "environment": environment,
                "default_project": settings.BILGEAPI_SOVEREIGN_DEFAULT_PROJECT
            }
        }

        if dry_run:
            logger.info(f"[Dry-run] Sovereign Repair Lab dispatch simulation successful for {repair_request_id}")
            return {
                "status": "SENT",
                "external_reference": "sovereign:case_dry-run-abc",
                "raw_response": {"case_id": "case_dry-run-abc", "status": "CREATED"}
            }

        url = f"{settings.BILGEAPI_SOVEREIGN_BASE_URL.rstrip('/')}/repairs"
        headers = {
            "X-API-Key": settings.BILGEAPI_SOVEREIGN_API_KEY,
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "BilgeAPI"
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=body_data, headers=headers)
            
            if 200 <= resp.status_code < 300:
                resp_json = resp.json()
                case_id = resp_json.get("case_id") or resp_json.get("id") or "created"
                ref = f"sovereign:case_{case_id}"
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
                    "error_message": f"Sovereign returned status code: {resp.status_code}. Response: {resp.text}"
                }
        except Exception as e:
            return {
                "status": "FAILED",
                "error_message": f"Sovereign dispatch exception: {str(e)}"
            }
