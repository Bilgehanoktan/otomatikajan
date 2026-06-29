import uuid
import httpx
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from apps.bilgeapi.models.database import BilgeAPIBridgeMappingModel
from services.observability.logging import get_logger

logger = get_logger("integrations.bilgeapi_bridge")

class BilgeAPIBridge:
    def __init__(self, db_session: AsyncSession, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.db = db_session
        default_url = "http://bilgeapi:8100" if os.getenv("DOCKER_CONTAINER") == "true" else "http://localhost:8100"
        self.base_url = (base_url or default_url).rstrip("/")
        self.api_key = api_key or "dev-test-key-001"

    async def forward_finding_intake(
        self,
        source_type: str,
        source_id: str,
        title: str,
        description: str,
        severity: str = "MEDIUM",
        evidence_summary: Optional[Dict[str, Any]] = None,
        recommended_action: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Forwards a platform finding or signal to BilgeAPI's /v1/watchdog/findings/intake.
        Uses BilgeAPIBridgeMappingModel for durable idempotency.
        """
        # 1. Check if mapping already exists (idempotency check)
        stmt = select(BilgeAPIBridgeMappingModel).where(
            BilgeAPIBridgeMappingModel.source_type == source_type,
            BilgeAPIBridgeMappingModel.source_id == source_id
        )
        result = await self.db.execute(stmt)
        mapping = result.scalar_one_or_none()

        if mapping and mapping.bilgeapi_finding_id:
            logger.info(
                f"Finding mapping already exists for {source_type}:{source_id} -> {mapping.bilgeapi_finding_id}"
            )
            return {
                "status": "success",
                "finding_id": mapping.bilgeapi_finding_id,
                "created": False,
                "deduped": True,
                "mapping_id": mapping.id
            }

        # 2. Call BilgeAPI intake endpoint
        url = f"{self.base_url}/v1/watchdog/findings/intake"
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "source_type": source_type,
            "source_id": source_id,
            "title": title,
            "description": description,
            "severity": severity.upper(),
            "evidence_summary": evidence_summary or {},
            "recommended_action": recommended_action,
            "tenant_id": tenant_id
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
        except Exception as e:
            logger.error(f"Failed to forward finding intake to BilgeAPI: {e}")
            raise RuntimeError(f"BilgeAPI connection failed: {e}") from e

        finding_id = data.get("finding_id")
        if not finding_id:
            raise ValueError(f"Invalid response from BilgeAPI: {data}")

        # 3. Create mapping record
        if not mapping:
            mapping = BilgeAPIBridgeMappingModel(
                id=f"map_{uuid.uuid4().hex[:12]}",
                source_type=source_type,
                source_id=source_id,
                bilgeapi_finding_id=finding_id,
                status="FORWARDED"
            )
            self.db.add(mapping)
        else:
            mapping.bilgeapi_finding_id = finding_id
            mapping.status = "FORWARDED"
        
        await self.db.commit()

        return {
            "status": "success",
            "finding_id": finding_id,
            "created": data.get("created", False),
            "deduped": data.get("deduped", False),
            "mapping_id": mapping.id
        }

    async def associate_improvement_flow(
        self,
        source_type: str,
        source_id: str,
        research_id: Optional[str] = None,
        proposal_id: Optional[str] = None,
        pr_draft_id: Optional[str] = None,
        verification_id: Optional[str] = None,
        ledger_chain_id: Optional[str] = None
    ) -> None:
        """
        Updates the durable mapping with downstream Improvement flow entities from BilgeAPI.
        """
        stmt = select(BilgeAPIBridgeMappingModel).where(
            BilgeAPIBridgeMappingModel.source_type == source_type,
            BilgeAPIBridgeMappingModel.source_id == source_id
        )
        result = await self.db.execute(stmt)
        mapping = result.scalar_one_or_none()
        if not mapping:
            raise ValueError(f"Mapping not found for {source_type}:{source_id}")

        if research_id:
            mapping.bilgeapi_research_id = research_id
        if proposal_id:
            mapping.bilgeapi_proposal_id = proposal_id
        if pr_draft_id:
            mapping.bilgeapi_pr_draft_id = pr_draft_id
        if verification_id:
            mapping.bilgeapi_verification_id = verification_id
        if ledger_chain_id:
            mapping.bilgeapi_ledger_chain_id = ledger_chain_id

        await self.db.commit()
