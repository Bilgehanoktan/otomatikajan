import hashlib
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from libs.db.session import get_db, get_db_ctx
from libs.db.models.compliance_models import RetentionPolicy, AuditBundle, EvidenceSeal
from libs.db.models.lineage_models import DecisionLineage, PolicyEvolution
from libs.db.models.governance_models import ProductionSignoff, ValidationResult

class ComplianceService:
    @staticmethod
    async def get_retention_policy(category: str) -> Optional[RetentionPolicy]:
        async with get_db_ctx() as session:
            result = await session.execute(
                select(RetentionPolicy).where(RetentionPolicy.data_category == category)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def create_retention_policy(category: str, hot: int, warm: int, cold: int, description: str = None) -> RetentionPolicy:
        async with get_db_ctx() as session:
            policy = RetentionPolicy(
                data_category=category,
                hot_retention_days=hot,
                warm_retention_days=warm,
                cold_retention_days=cold,
                description=description
            )
            session.add(policy)
            await session.commit()
            await session.refresh(policy)
            return policy

    @staticmethod
    async def generate_audit_bundle(name: str, purpose: str, start_time: datetime, end_time: datetime, operator_id: str) -> AuditBundle:
        """
        Creates a sealed audit bundle of evidence within a time range.
        Gather real data from lineage, evolution, and signoffs.
        """
        async with get_db_ctx() as session:
            # 1. Collect Lineage
            lineage_res = await session.execute(
                select(DecisionLineage).where(
                    and_(
                        DecisionLineage.created_at >= start_time,
                        DecisionLineage.created_at <= end_time
                    )
                )
            )
            lineage_data = [
                {"id": str(d.id), "type": d.decision_type, "rationale": d.rationale, "integrity": d.integrity_hash}
                for d in lineage_res.scalars().all()
            ]

            # 2. Collect Policy Evolutions
            evolution_res = await session.execute(
                select(PolicyEvolution).where(
                    and_(
                        PolicyEvolution.created_at >= start_time,
                        PolicyEvolution.created_at <= end_time
                    )
                )
            )
            evolution_data = [
                {"id": str(e.id), "key": e.policy_key, "version": e.version, "reason": e.change_reason}
                for e in evolution_res.scalars().all()
            ]

            # 3. Collect Signoffs
            signoff_res = await session.execute(
                select(ProductionSignoff).where(
                    and_(
                        ProductionSignoff.created_at >= start_time,
                        ProductionSignoff.created_at <= end_time
                    )
                )
            )
            signoff_data = [
                {"id": str(s.id), "component": s.component_name, "status": s.status, "approver": str(s.approver_id)}
                for s in signoff_res.scalars().all()
            ]

            evidence_data = {
                "summary": {
                    "lineage_count": len(lineage_data),
                    "evolution_count": len(evolution_data),
                    "signoff_count": len(signoff_data)
                },
                "lineage_ids": [d["id"] for d in lineage_data],
                "evolution_ids": [e["id"] for e in evolution_data],
                "signoff_ids": [s["id"] for s in signoff_data],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Simple integrity hash of name + purpose + metadata string
            raw_bundle = f"{name}|{purpose}|{json.dumps(evidence_data, sort_keys=True)}"
            integrity_hash = hashlib.sha256(raw_bundle.encode()).hexdigest()

            bundle = AuditBundle(
                bundle_name=name,
                purpose=purpose,
                start_time=start_time,
                end_time=end_time,
                evidence_metadata=evidence_data,
                integrity_hash=integrity_hash,
                created_by=operator_id
            )
            session.add(bundle)
            await session.commit()
            await session.refresh(bundle)
            return bundle

    @staticmethod
    async def list_audit_bundles() -> List[AuditBundle]:
        async with get_db_ctx() as session:
            result = await session.execute(select(AuditBundle).order_by(AuditBundle.created_at.desc()))
            return list(result.scalars().all())

    @staticmethod
    async def seal_evidence(table: str, target_id: Any, signer_id: str) -> EvidenceSeal:
        """Adds a cryptographic seal to a specific record."""
        seal_payload = f"{table}|{target_id}|{datetime.now(timezone.utc).isoformat()}"
        signature = hashlib.sha256(seal_payload.encode()).hexdigest()
        
        async with get_db_ctx() as session:
            seal = EvidenceSeal(
                target_table=table,
                target_id=target_id,
                seal_signature=signature,
                signer_id=signer_id
            )
            session.add(seal)
            await session.commit()
            await session.refresh(seal)
            return seal
