import hashlib
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
# from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.session import get_db, get_db_ctx
# from libs.db.models.lineage_models import DecisionLineage, PolicyEvolution
from services.observability.logging import get_logger
from services.governance.proof_fabric import ProofFabric
# from libs.db.models.governance_models import ProofEventType, GovernorDomain

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
        meta_data: Optional[Dict[str, Any]] = None,
        db: Optional[Any] = None
    ) -> Any:
        """
        Otonom bir kararı soyağacına kaydeder. 
        Her karar bir 'integrity_hash' ile mühürlenir.
        """
        if db is None:
            async with get_db_ctx() as session:
                return await LineageService._log_decision_core(
                    session, decision_type, component_name, rationale, outcome,
                    parent_id, root_id, trigger_event, confidence_score, meta_data
                )
        else:
            return await LineageService._log_decision_core(
                db, decision_type, component_name, rationale, outcome,
                parent_id, root_id, trigger_event, confidence_score, meta_data
            )

    @staticmethod
    async def _log_decision_core(
        db: Any,
        decision_type: str,
        component_name: str,
        rationale: str,
        outcome: Optional[str] = None,
        parent_id: Optional[str] = None,
        root_id: Optional[str] = None,
        trigger_event: Optional[Dict[str, Any]] = None,
        confidence_score: float = 1.0,
        meta_data: Optional[Dict[str, Any]] = None
    ) -> Any:
        from libs.db.models.lineage_models import DecisionLineage
        from libs.db.models.governance_models import ProofEventType
        # Hash calculation for Proof Fabric
        parent_hash = ""
        if parent_id:
            # Use db.get for async session compatibility
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
        # Flush to get ID but don't commit if external session
        await db.flush()

        # Phase 11: Record Proof Event
        try:
            from sqlalchemy.ext.asyncio import AsyncSession as _AsyncSession
            if isinstance(db, _AsyncSession):
                # USE ASYNC FABRIC - NO NEW SESSION
                fabric = ProofFabric(db)
                await fabric.record_governance_event_async(
                    event_type=ProofEventType.GOVERNOR_DECISION if decision_type != "META_GOVERNOR_DECISION" else ProofEventType.META_DECISION,
                    domain=None,
                    entity_id=str(lineage.id),
                    payload={
                        "decision_type": decision_type,
                        "rationale": rationale,
                        "outcome": outcome,
                        "integrity_hash": integrity_hash
                    },
                    actor="LineageService"
                )
            else:
                # Fallback to sync only if absolutely necessary and not on SQLite or not async
                from libs.db.session import SessionLocal
                with SessionLocal() as sync_db:
                    fabric = ProofFabric(sync_db)
                    fabric.record_governance_event(
                        event_type=ProofEventType.GOVERNOR_DECISION if decision_type != "META_GOVERNOR_DECISION" else ProofEventType.META_DECISION,
                        domain=None,
                        entity_id=str(lineage.id),
                        payload={
                            "decision_type": decision_type,
                            "rationale": rationale,
                            "outcome": outcome,
                            "integrity_hash": integrity_hash
                        },
                        actor="LineageService"
                    )
        except Exception as e:
            logger.error(f"Failed to record Proof Event for decision {lineage.id}: {str(e)}")

        logger.info(f"Lineage Logged (Sealed): {decision_type} ({outcome}) for {component_name} (ID: {lineage.id})")
        return lineage

    @staticmethod
    async def log_policy_change(
        policy_key: str,
        new_value: Any,
        previous_value: Optional[Any] = None,
        change_reason: Optional[str] = None,
        author_id: Optional[str] = "SYSTEM",
        decision_id: Optional[str] = None,
        db: Optional[Any] = None
    ) -> Any:
        """Yönetişim politikası değişikliğini kaydeder."""
        if db is None:
            async with get_db_ctx() as session:
                return await LineageService._log_policy_core(
                    session, policy_key, new_value, previous_value,
                    change_reason, author_id, decision_id
                )
        else:
            return await LineageService._log_policy_core(
                db, policy_key, new_value, previous_value,
                change_reason, author_id, decision_id
            )

    @staticmethod
    async def _log_policy_core(
        db: Any,
        policy_key: str,
        new_value: Any,
        previous_value: Optional[Any] = None,
        change_reason: Optional[str] = None,
        author_id: Optional[str] = "SYSTEM",
        decision_id: Optional[str] = None
    ) -> Any:
        from libs.db.models.lineage_models import PolicyEvolution
        from libs.db.models.governance_models import ProofEventType, GovernorDomain
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
        await db.flush()

        # Phase 11: Record Proof Event
        try:
            from sqlalchemy.ext.asyncio import AsyncSession as _AsyncSession
            if isinstance(db, _AsyncSession):
                fabric = ProofFabric(db)
                await fabric.record_governance_event_async(
                    event_type=ProofEventType.POLICY_EVOLUTION,
                    domain=GovernorDomain.POLICY,
                    entity_id=str(evolution.id),
                    payload={
                        "policy_key": policy_key,
                        "new_value": new_value,
                        "change_reason": change_reason
                    },
                    actor=author_id
                )
            else:
                from libs.db.session import SessionLocal
                with SessionLocal() as sync_db:
                    fabric = ProofFabric(sync_db)
                    fabric.record_governance_event(
                        event_type=ProofEventType.POLICY_EVOLUTION,
                        domain=GovernorDomain.POLICY,
                        entity_id=str(evolution.id),
                        payload={
                            "policy_key": policy_key,
                            "new_value": new_value,
                            "change_reason": change_reason
                        },
                        actor=author_id
                    )
        except Exception as e:
            logger.error(f"Failed to record Proof Event for policy change {evolution.id}: {str(e)}")

        logger.info(f"Policy Evolved: {policy_key} to {new_value}")
        return evolution

    # ── Soft CEO: Structured Decision Logging ──────────────────
    @staticmethod
    async def log_soft_ceo_decision(
        recommended_action: str,
        risk_class: str,
        pending_reason: str,
        target_type: str,
        target_id: str,
        rationale: str,
        confidence_score: float = 0.5,
        staleness_hours: float = 0.0,
        parent_id: Optional[str] = None,
        extra_meta: Optional[Dict[str, Any]] = None,
        db: Optional[Any] = None
    ) -> Any:
        meta = {
            "risk_class": risk_class,
            "pending_reason": pending_reason,
            "recommended_action": recommended_action,
            "target_type": target_type,
            "target_id": target_id,
            "staleness_hours": round(staleness_hours, 2),
            "agent": "soft_ceo",
            **(extra_meta or {})
        }

        return await LineageService.log_decision(
            decision_type="SOFT_CEO_TRIAGE",
            component_name="soft_ceo",
            rationale=rationale,
            outcome=recommended_action,
            parent_id=parent_id,
            trigger_event={"target": f"{target_type}:{target_id}", "reason": pending_reason},
            confidence_score=confidence_score,
            meta_data=meta,
            db=db
        )

    @staticmethod
    async def log_meta_governor_decision(
        project_id: Any,
        domain_decisions: Dict[str, Dict[str, Any]],
        final_decision: Dict[str, Any],
        conflicts: List[Dict[str, Any]],
        constraints: List[str],
        db: Optional[Any] = None
    ) -> Any:
        meta = {
            "domain_decisions": domain_decisions,
            "conflicts": conflicts,
            "constraints": constraints,
            "winning_domain": final_decision.get("domain"),
            "risk_score": final_decision.get("risk_score"),
            "agent": "meta_governor"
        }
        
        return await LineageService.log_decision(
            decision_type="META_GOVERNOR_DECISION",
            component_name="meta_governor",
            rationale=f"Final meta-decision for project {project_id}",
            outcome=final_decision["recommended_decision"],
            trigger_event={"project_id": str(project_id)},
            meta_data=meta,
            db=db
        )

    @staticmethod
    async def log_governor_resilience_event(
        domain: str,
        event_type: str,
        details: str,
        meta: Optional[Dict[str, Any]] = None,
        db: Optional[Any] = None
    ) -> Any:
        return await LineageService.log_decision(
            decision_type="GOVERNOR_RESILIENCE",
            component_name=f"governor:{domain.lower()}",
            rationale=details,
            outcome=event_type,
            trigger_event={"domain": domain, "event": event_type},
            meta_data=meta or {},
            db=db
        )

    @staticmethod
    async def log_policy_evolution_decision(
        evolution_id: str,
        policy_key: str,
        event_type: str,
        details: str,
        meta: Optional[Dict[str, Any]] = None,
        db: Optional[Any] = None
    ) -> Any:
        return await LineageService.log_decision(
            decision_type="POLICY_EVOLUTION",
            component_name="governor_policy_engine",
            rationale=details,
            outcome=event_type,
            trigger_event={"evolution_id": evolution_id, "policy_key": policy_key},
            meta_data=meta or {},
            db=db
        )

    @staticmethod
    async def log_governor_alert(
        alert_id: str,
        alert_type: str,
        severity: str,
        status: str,
        summary: str,
        db: Optional[Any] = None
    ) -> Any:
        return await LineageService.log_decision(
            decision_type="GOVERNOR_ALERT",
            component_name="governor_observability",
            rationale=summary,
            outcome=status,
            trigger_event={"alert_id": alert_id, "type": alert_type, "severity": severity},
            db=db
        )

    @staticmethod
    async def log_governor_drift(
        drift_id: str,
        drift_type: str,
        score: float,
        summary: str,
        db: Optional[Any] = None
    ) -> Any:
        return await LineageService.log_decision(
            decision_type="GOVERNOR_DRIFT",
            component_name="governor_drift_detector",
            rationale=summary,
            outcome="DETECTED",
            trigger_event={"drift_id": drift_id, "type": drift_type, "score": score},
            db=db
        )

    # ── Faz 12: Fleet Orchestration Logging ──────────────────
    @staticmethod
    async def log_fleet_event(
        event_type: str,
        target_id: str,
        details: str,
        meta: Optional[Dict[str, Any]] = None,
        actor: str = "FleetScheduler",
        db: Optional[Any] = None
    ) -> Any:
        """Logs fleet orchestration events (assignment, rebalance, etc)."""
        from libs.db.models.governance_models import ProofEventType
        # Map fleet string event to ProofEventType
        proof_map = {
            "AGENT_ASSIGNED": ProofEventType.AGENT_ASSIGNED,
            "AGENT_RELEASED": ProofEventType.AGENT_RELEASED,
            "CLUSTER_FROZEN": ProofEventType.CLUSTER_FROZEN,
            "FLEET_REBALANCED": ProofEventType.FLEET_REBALANCED,
            "BUDGET_BLOCK": ProofEventType.BUDGET_BLOCK,
            "AGENT_QUARANTINED": ProofEventType.AGENT_QUARANTINED
        }
        
        proof_type = proof_map.get(event_type, ProofEventType.RUNTIME_EVENT)

        lineage = await LineageService.log_decision(
            decision_type="FLEET_EVENT",
            component_name="fleet_orchestra",
            rationale=details,
            outcome=event_type,
            trigger_event={"target_id": target_id, "event": event_type},
            meta_data=meta or {},
            db=db
        )
        
        # Explicit Proof Event recording for fleet
        try:
            from libs.db.session import SessionLocal
            with SessionLocal() as sync_db:
                fabric = ProofFabric(sync_db)
                fabric.record_governance_event(
                    event_type=proof_type,
                    domain=None,
                    entity_id=target_id,
                    payload={
                        "event": event_type,
                        "details": details,
                        "meta": meta or {}
                    },
                    actor=actor
                )
        except Exception as e:
            logger.error(f"Failed to record Fleet Proof Event: {str(e)}")
            
        return lineage
