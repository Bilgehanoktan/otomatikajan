import logging
import hashlib
import json
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from libs.db.models.ui_repair_models import (
    UIFederatedEvidenceRecord, UITenantProjectBinding
)
from libs.db.models.core_models import SovereignEvidence

logger = logging.getLogger(__name__)

class FederatedEvidenceLedger:
    """
    Synchronizes evidence hashes across clusters to ensure global audit integrity.
    """

    @staticmethod
    async def sync_evidence_to_ledger(db: AsyncSession, evidence_id: str) -> Optional[UIFederatedEvidenceRecord]:
        """Publishes a local evidence record to the federated ledger."""
        stmt = select(SovereignEvidence).where(SovereignEvidence.id == evidence_id)
        evidence = (await db.execute(stmt)).scalar_one_or_none()
        
        if not evidence:
            return None

        # Get tenant/cluster context from payload or mapping
        payload = evidence.payload or {}
        project_key = payload.get("project_key")
        
        # Resolve binding
        binding_stmt = select(UITenantProjectBinding).where(UITenantProjectBinding.project_key == project_key)
        binding = (await db.execute(binding_stmt)).scalar_one_or_none()
        
        tenant_key = binding.tenant_key if binding else "GLOBAL"
        cluster_key = binding.cluster_key if binding else "DEFAULT"

        record = UIFederatedEvidenceRecord(
            tenant_key=tenant_key,
            cluster_key=cluster_key,
            project_key=project_key or "unknown",
            source_evidence_id=str(evidence.id),
            evidence_type=evidence.evidence_type,
            evidence_hash=evidence.provenance_hash or "no-hash",
            sync_status="SYNCED"
        )
        db.add(record)
        await db.commit()
        logger.info(f"Evidence {evidence_id} synced to federated ledger for tenant {tenant_key}")
        return record

    @staticmethod
    async def list_federated_evidence(
        db: AsyncSession, 
        tenant_key: Optional[str] = None, 
        cluster_key: Optional[str] = None
    ) -> List[UIFederatedEvidenceRecord]:
        """Lists federated evidence records with filtering."""
        stmt = select(UIFederatedEvidenceRecord)
        if tenant_key:
            stmt = stmt.where(UIFederatedEvidenceRecord.tenant_key == tenant_key)
        if cluster_key:
            stmt = stmt.where(UIFederatedEvidenceRecord.cluster_key == cluster_key)
            
        result = await db.execute(stmt)
        return list(result.scalars().all())
