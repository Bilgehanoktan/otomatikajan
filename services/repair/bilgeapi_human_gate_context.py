import httpx
from typing import Dict, Any, Optional
from services.observability.logging import get_logger

logger = get_logger("repair.bilgeapi_human_gate_context")

class BilgeAPIHumanGateVerifier:
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        default_url = "http://bilgeapi:8100" if os.getenv("DOCKER_CONTAINER") == "true" else "http://localhost:8100"
        self.base_url = (base_url or default_url).rstrip("/")
        self.api_key = api_key or "dev-test-key-001"

    async def verify_ledger_integrity(self, chain_id: str) -> Dict[str, Any]:
        """
        Queries BilgeAPI's review-ledger verification endpoint to ensure chain integrity.
        """
        url = f"{self.base_url}/v1/review-ledger/chains/{chain_id}/verify"
        headers = {
            "X-API-Key": self.api_key
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers)
                if response.status_code == 404:
                    # If chain doesn't exist yet, we treat it as valid (no entries recorded yet)
                    logger.info(f"Ledger chain {chain_id} not found, assuming valid (empty).")
                    return {"valid": True, "entry_count": 0, "issues": []}
                
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to verify review ledger integrity for chain {chain_id}: {e}")
            # Security-first: If we can't verify, we fail closed (not valid)
            return {"valid": False, "entry_count": 0, "issues": [{"type": "CONNECTION_FAILED", "detail": str(e)}]}

    async def assert_approval_allowed(self, chain_id: str) -> None:
        """
        Asserts that ledger integrity is intact. Raises a ValueError if the ledger is invalid.
        """
        result = await self.verify_ledger_integrity(chain_id)
        if not result.get("valid", False):
            issues = result.get("issues", [])
            issue_details = "; ".join([str(i) for i in issues])
            logger.error(f"Approval blocked: Ledger chain {chain_id} is corrupted. Issues: {issue_details}")
            raise ValueError(f"Approval blocked: Ledger chain integrity verification failed. Issues: {issue_details}")
