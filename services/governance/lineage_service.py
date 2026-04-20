import hashlib
import json
from typing import Dict, Any, Optional
from datetime import datetime
from libs.db.session import get_db, get_db_ctx
from libs.db.models.lineage_models import DecisionLineage, PolicyEvolution
from services.observability.logging import get_logger

logger = get_logger("governance.lineage")

class LineageService:
    @staticmethod
    async def log_decision(
        decision_type: str,
        component_name: str,
        rationale: str,
        outcome: Optional[str] = None,
        parent_id: Optional[str] = None,
        root_id: Optional[str] = None,
        trigger_event: Optional[Dict[str, Any]] = None,
        confidence_score: float = 1.0,
        meta_data: Optional[Dict[str, Any]] = None
    ) -> DecisionLineage:
        """
        Otonom bir kararı soyağacına kaydeder. 
        Her karar bir 'integrity_hash' ile mühürlenir.
        """
        async with get_db_ctx() as db:
            # Hash calculation for Proof Fabric
            parent_hash = ""
            if parent_id:
                parent_result = await db.get(DecisionLineage, parent_id)
                if parent_result:
                    parent_hash = parent_result.integrity_hash or ""

            # Payload for hash
            payload = f"{decision_type}|{component_name}|{rationale}|{outcome or ''}|{parent_hash}"
            integrity_hash = hashlib.sha256(payload.encode()).hexdigest()

            lineage = DecisionLineage(
                decision_type=decision_type,
                component_name=component_name,
                rationale=rationale,
                outcome=outcome,
                parent_id=parent_id,
                root_id=root_id or parent_id,
                trigger_event=trigger_event,
                confidence_score=confidence_score,
                integrity_hash=integrity_hash,
                meta_data=meta_data or {}
            )
            db.add(lineage)
            await db.commit()
            await db.refresh(lineage)
            logger.info(f"Lineage Logged (Sealed): {decision_type} ({outcome}) for {component_name} (ID: {lineage.id})")
            return lineage

    @staticmethod
    async def log_policy_change(
        policy_key: str,
        new_value: Any,
        previous_value: Optional[Any] = None,
        change_reason: Optional[str] = None,
        author_id: Optional[str] = "SYSTEM",
        decision_id: Optional[str] = None
    ) -> PolicyEvolution:
        """Yönetişim politikası değişikliğini kaydeder."""
        async with get_session() as db:
            evolution = PolicyEvolution(
                policy_key=policy_key,
                version="v" + str(int(datetime.now().timestamp())),
                previous_value=previous_value,
                new_value=new_value,
                change_reason=change_reason,
                author_id=author_id,
                decision_id=decision_id
            )
            db.add(evolution)
            await db.commit()
            await db.refresh(evolution)
            logger.info(f"Policy Evolved: {policy_key} to {new_value}")
            return evolution
