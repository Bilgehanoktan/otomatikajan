"""
Sovereign AGI — Phase 30
services/compliance/compliance_service.py
Service for managing data retention, evidence tiering, and integrity sealing.
"""

import hashlib
import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import select, delete, update
from libs.db.session import AsyncSessionLocal
from libs.db.models.compliance_models import RetentionPolicy, AuditBundle, EvidenceSeal
from libs.db.models.lineage_models import DecisionLineage
from services.observability.logging import get_logger

logger = get_logger("compliance.fabric")

class ComplianceService:
    @staticmethod
    async def get_retention_policy(category: str) -> Optional[RetentionPolicy]:
        """Kategoriye gÃ¶re saklama politikasÄ±nÄ± dÃ¶ner."""
        async with AsyncSessionLocal() as session:
            stmt = select(RetentionPolicy).where(RetentionPolicy.data_category == category)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @staticmethod
    async def initialize_defaults():
        """VarsayÄ±lan kurumsal saklama politikalarÄ±nÄ± yÃ¼kler (Phase 30)."""
        defaults = [
            {"data_category": "TELEMETRY", "hot": 90, "warm": 365, "cold": 1095, "perm": False},
            {"data_category": "DRILL_LOGS", "hot": 30, "warm": 90, "cold": 180, "perm": False},
            {"data_category": "DECISION_LINEAGE", "hot": 365, "warm": 1095, "cold": 1825, "perm": True},
            {"data_category": "CONSTITUTION", "hot": 365, "warm": 1095, "cold": 1825, "perm": True},
            {"data_category": "SIGNOFFS", "hot": 365, "warm": 1095, "cold": 1825, "perm": True},
        ]
        
        async with AsyncSessionLocal() as session:
            for d in defaults:
                stmt = select(RetentionPolicy).where(RetentionPolicy.data_category == d["data_category"])
                existing = await session.execute(stmt)
                if not existing.scalar_one_or_none():
                    new_p = RetentionPolicy(
                        data_category=d["data_category"],
                        hot_retention_days=d["hot"],
                        warm_retention_days=d["warm"],
                        cold_retention_days=d["cold"],
                        is_permanent=d["perm"]
                    )
                    session.add(new_p)
            await session.commit()
            logger.info("Compliance retention defaults initialized.")

    @staticmethod
    async def seal_record(table_name: str, record_id: str, content: Dict[str, Any]) -> str:
        """Bir kaydÄ±n iÃ§eriÄini hash'leyerek mÃ¼hÃ¼rler (Evidence Seal)."""
        content_str = json.dumps(content, sort_keys=True)
        h = hashlib.sha256(content_str.encode()).hexdigest()
        
        async with AsyncSessionLocal() as session:
            seal = EvidenceSeal(
                target_table=table_name,
                target_id=record_id,
                seal_signature=h,
                signer_id="SYSTEM_FABRIC"
            )
            session.add(seal)
            
            # Lineage tablosu ise kendi integrity_hash alanÄ±nÄ± da gÃ¼ncelle
            if table_name == "decision_lineage":
                stmt = update(DecisionLineage).where(DecisionLineage.id == record_id).values(integrity_hash=h)
                await session.execute(stmt)
                
            await session.commit()
            logger.info(f"Record {record_id} in {table_name} sealed with hash: {h[:8]}...")
            return h

    @staticmethod
    async def create_audit_bundle(name: str, start: datetime, end: datetime, creator: str) -> AuditBundle:
        """Belirli bir zaman aralÄ±ÄÄ± iÃ§in denetim paketi oluÅturur."""
        
        async with AsyncSessionLocal() as session:
            # Evidence Collection (Phase 30 Improvement)
            # Find evidence seals within range
            stmt = select(EvidenceSeal).where(EvidenceSeal.created_at.between(start, end))
            res = await session.execute(stmt)
            seals = res.scalars().all()
            
            evidence_data = {
                "status": "GENERATED",
                "scope": "PHASE_30_INSTITUTIONAL",
                "evidence_count": len(seals),
                "seals": [s.id.hex for s in seals[:10]], # Sample for meta
                "bundle_id": f"AUDIT-{uuid.uuid4().hex[:8].upper()}"
            }
            
            bundle = AuditBundle(
                bundle_name=name,
                start_time=start,
                end_time=end,
                evidence_metadata=evidence_data,
                integrity_hash="SEALED", # In real: hash of the concatenated evidence
                created_by=creator
            )
            session.add(bundle)
            await session.commit()
            await session.refresh(bundle)
            logger.info(f"Audit Bundle {bundle.id} generated with {len(seals)} evidence points.")
            return bundle

    @staticmethod
    async def enforce_retention():
        """GeÃ§miÅ verileri politikalara gÃ¶re temizler (Cleanup Job)."""
        logger.info("Running compliance retention enforcement...")
        
        async with AsyncSessionLocal() as session:
            # 1. Get all policies
            res = await session.execute(select(RetentionPolicy))
            policies = res.scalars().all()
            
            for policy in policies:
                if policy.is_permanent:
                    continue
                
                # Cleanup logic based on data category
                cutoff = datetime.now(timezone.utc) - timedelta(days=policy.cold_retention_days)
                
                if policy.data_category == "TELEMETRY":
                    # For Phase 30, we consider ValidationResult as "HAM TELEMETRY"
                    from libs.db.models.governance_models import ValidationResult
                    stmt = delete(ValidationResult).where(ValidationResult.created_at < cutoff)
                    await session.execute(stmt)
                    
                elif policy.data_category == "DRILL_LOGS":
                    # Assume VerifierResult are high-volume logs from drills/repairs
                    from libs.db.models.repair_models import VerifierResult
                    stmt = delete(VerifierResult).where(VerifierResult.timestamp < cutoff)
                    await session.execute(stmt)
            
            await session.commit()
            logger.info("Compliance retention enforcement completed.")
