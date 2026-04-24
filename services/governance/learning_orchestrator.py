"""
Sovereign AGI — Phase 31
services/governance/learning_orchestrator.py
Orchestrates autonomous learning from incidents and repair cycles.
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from libs.db.session import get_db_ctx, AsyncSessionLocal
from libs.db.models.learning_models import ErrorFingerprint, LearningRecord, StrategyMemory, NegativePatternMemory
from services.observability.logging import get_logger

logger = get_logger("governance.learning")

class LearningOrchestrator:
    @staticmethod
    async def record_learning(
        incident_data: Dict[str, Any],
        outcome_data: Dict[str, Any],
        db: Optional[AsyncSession] = None
    ) -> LearningRecord:
        """
        Her çözülmüş incident, approval veya repair döngüsü sonrası öğrenme kaydı oluşturur.
        """
        if db is None:
            async with get_db_ctx() as session:
                res = await LearningOrchestrator._record_core(session, incident_data, outcome_data)
                await session.commit()
                return res
        else:
            return await LearningOrchestrator._record_core(db, incident_data, outcome_data)

    @staticmethod
    async def _record_core(db: AsyncSession, incident: Dict[str, Any], outcome: Dict[str, Any]) -> LearningRecord:
        # 1. Fingerprint create or update
        fingerprint = await LearningOrchestrator._get_or_create_fingerprint(db, incident)
        
        # 2. Update Strategy Memory
        strategy_name = outcome.get("strategy_used", "unknown")
        error_family = fingerprint.error_family
        component = fingerprint.component
        
        is_success = outcome.get("final_outcome") == "SUCCESS"
        rollback = outcome.get("rollback_required", False)
        
        await LearningOrchestrator._update_strategy_memory(
            db, component, error_family, strategy_name, 
            is_success,
            outcome.get("repair_latency_s", 0.0),
            outcome.get("verification_score", 0.0),
            outcome.get("cost_usd", 0.0),
            rollback,
            outcome.get("operator_override", False)
        )
        
        # 3. Handle Negative Patterns
        if not is_success or rollback:
            await LearningOrchestrator._update_negative_pattern(
                db, fingerprint.id, component, strategy_name,
                outcome.get("failure_reason", outcome.get("root_cause")),
                outcome.get("rollback_reason"),
                outcome.get("blast_radius", "medium")
            )
        
        # 4. Create Learning Record
        record = LearningRecord(
            fingerprint_id=fingerprint.id,
            incident_id=incident.get("id"),
            workflow_id=outcome.get("workflow_id"),
            project_id=incident.get("project_id"),
            approval_id=outcome.get("approval_id"),
            lineage_id=outcome.get("lineage_id"),
            root_cause=outcome.get("root_cause", "unknown"),
            proposed_fix_type=outcome.get("proposed_fix_type", "code"),
            strategy_used=strategy_name,
            verification_score=outcome.get("verification_score", 0.0),
            canary_result=outcome.get("canary_result"),
            final_outcome=outcome.get("final_outcome", "SUCCESS"),
            rollback_required=rollback,
            operator_override=outcome.get("operator_override", False),
            repair_latency_s=outcome.get("repair_latency_s", 0.0),
            cost_usd=outcome.get("cost_usd", 0.0),
            confidence_after_resolution=outcome.get("confidence_after_resolution", 1.0),
            applied_patch=outcome.get("applied_patch"),
            integrity_hash=LearningOrchestrator._compute_integrity(incident, outcome)
        )
        
        db.add(record)
        await db.flush()
        
        logger.info(f"Learning Record Sealed: {record.id} for fingerprint {fingerprint.id}")
        return record

    @staticmethod
    async def _get_or_create_fingerprint(db: AsyncSession, incident: Dict[str, Any]) -> ErrorFingerprint:
        service = incident.get("service", "unknown")
        component = incident.get("component", incident.get("incident_type", "unknown"))
        exc_type = incident.get("exception_type", "GeneralError")
        msg = incident.get("message", "")
        
        normalized_msg = LearningOrchestrator._normalize_message(msg)
        
        fingerprint_payload = f"{service}|{component}|{exc_type}|{normalized_msg[:100]}"
        fp_hash = hashlib.sha256(fingerprint_payload.encode()).hexdigest()
        
        res = await db.execute(select(ErrorFingerprint).where(ErrorFingerprint.fingerprint_hash == fp_hash))
        fp = res.scalar_one_or_none()
        
        if fp:
            fp.recurrence_count += 1
            fp.last_seen_at = datetime.now(timezone.utc)
        else:
            fp = ErrorFingerprint(
                fingerprint_hash=fp_hash,
                error_family=LearningOrchestrator._infer_family(exc_type, msg),
                service=service,
                component=component,
                exception_type=exc_type,
                normalized_message=normalized_msg,
                severity=incident.get("severity", "medium"),
                risk_domain=incident.get("risk_domain", "general")
            )
            db.add(fp)
        
        await db.flush()
        return fp

    @staticmethod
    async def _update_strategy_memory(
        db: AsyncSession, component: str, family: str, strategy: str, 
        success: bool, latency: float, score: float, cost: float, 
        rollback: bool, operator_override: bool
    ):
        res = await db.execute(
            select(StrategyMemory).where(
                StrategyMemory.component == component,
                StrategyMemory.error_family == family,
                StrategyMemory.strategy_name == strategy
            )
        )
        mem = res.scalar_one_or_none()
        
        if not mem:
            mem = StrategyMemory(
                component=component,
                error_family=family,
                strategy_name=strategy,
                state="observed",
                success_count=0,
                failure_count=0,
                rollback_count=0,
                operator_reject_count=0,
                avg_repair_latency=0.0,
                avg_verification_score=0.0,
                avg_cost_usd=0.0,
                trust_score=0.5
            )
            db.add(mem)
            await db.flush() # Ensure it's attached and has values
        
        if success:
            mem.success_count += 1
            mem.last_success_at = datetime.now(timezone.utc)
        else:
            mem.failure_count += 1
            mem.last_failure_at = datetime.now(timezone.utc)
            
        if rollback:
            mem.rollback_count += 1
        
        if operator_override:
            mem.operator_reject_count += 1
            
        # Update metrics
        total = mem.success_count + mem.failure_count
        mem.avg_repair_latency = ((mem.avg_repair_latency * (total - 1)) + latency) / total
        mem.avg_verification_score = ((mem.avg_verification_score * (total - 1)) + score) / total
        mem.avg_cost_usd = ((mem.avg_cost_usd * (total - 1)) + cost) / total
        
        # Trust Score Logic (PEL-SIF-03 Hardening)
        success_rate = mem.success_count / total
        # Rollback is extremely expensive in terms of trust
        rollback_penalty = (mem.rollback_count / total) * 3.0
        # Human rejection is a strong signal of misaligned strategy
        reject_penalty = (mem.operator_reject_count / total) * 2.0
        
        mem.trust_score = max(0.0, success_rate - rollback_penalty - reject_penalty)
        
        # State promotion logic (PEL-SIF-03)
        # Recurrence Gate: At least 3 successes for Candidate status
        if mem.state == "observed" and mem.success_count >= 3 and mem.trust_score >= 0.7:
            mem.state = "candidate"
        # Safety Gate: At least 10 successes and ZERO rollbacks for Trusted status
        elif mem.state == "candidate" and mem.success_count >= 10 and mem.trust_score >= 0.9 and mem.rollback_count == 0:
            mem.state = "trusted"
        # Demotion logic: If trust drops significantly, demote back to observed
        elif mem.trust_score < 0.4:
            mem.state = "observed"
            
        await db.flush()

    @staticmethod
    async def _update_negative_pattern(
        db: AsyncSession, fingerprint_id: Any, component: str, strategy: str,
        failure_reason: str, rollback_reason: str, blast_radius: str
    ):
        res = await db.execute(
            select(NegativePatternMemory).where(
                NegativePatternMemory.fingerprint_id == fingerprint_id,
                NegativePatternMemory.strategy_name == strategy
            )
        )
        pat = res.scalar_one_or_none()
        
        if pat:
            pat.occurrence_count += 1
            pat.last_seen_at = datetime.now(timezone.utc)
            pat.penalty_weight *= 1.2 # Increasing penalty
        else:
            pat = NegativePatternMemory(
                fingerprint_id=fingerprint_id,
                component=component,
                strategy_name=strategy,
                failure_reason=failure_reason,
                rollback_reason=rollback_reason,
                blast_radius=blast_radius,
                penalty_weight=1.5,
                occurrence_count=1
            )
            db.add(pat)
        await db.flush()

    @staticmethod
    def _normalize_message(msg: str) -> str:
        import re
        # Remove UUIDs
        msg = re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '<UUID>', msg)
        # Remove hex IDs
        msg = re.sub(r'0x[0-9a-f]+', '<HEX>', msg)
        # Remove numbers (optional, might be too aggressive)
        # msg = re.sub(r'\d+', '<NUM>', msg)
        return msg

    @staticmethod
    def _compute_integrity(incident: Dict, outcome: Dict) -> str:
        payload = f"{incident.get('id')}|{outcome.get('final_outcome')}|{datetime.now(timezone.utc).isoformat()}"
        return hashlib.sha256(payload.encode()).hexdigest()

    @staticmethod
    def _infer_family(exc_type: str, msg: str) -> str:
        msg_l = msg.lower()
        if "lock" in msg_l or "deadlock" in msg_l: return "DATABASE_LOCK"
        if "timeout" in msg_l: return "TIMEOUT"
        if "permission" in msg_l or "unauthorized" in msg_l: return "AUTH_FAILURE"
        if "connection" in msg_l: return "NETWORK_FAILURE"
        if "null" in msg_l or "none" in msg_l: return "NULL_POINTER"
        return exc_type.upper()

    @staticmethod
    async def get_strategy_memory(strategy_name: str) -> Optional[StrategyMemory]:
        """Fetches memory for a specific strategy across all components."""
        async with get_db_ctx() as db:
            res = await db.execute(select(StrategyMemory).where(StrategyMemory.strategy_name == strategy_name))
            # Returns the one with highest trust or most recent if multiple (though name is unique in many cases)
            return res.scalars().first()

    @staticmethod
    async def get_global_learning_stats() -> Dict[str, Any]:
        """Aggregates learning signals for system-wide self-tuning."""
        async with get_db_ctx() as db:
            # Success vs Failure ratio
            res_total = await db.execute(select(StrategyMemory))
            memories = res_total.scalars().all()
            
            total_success = sum(m.success_count for m in memories)
            total_failure = sum(m.failure_count for m in memories)
            total_rollback = sum(m.rollback_count for m in memories)
            total_reject = sum(m.operator_reject_count for m in memories)
            
            success_rate = total_success / (total_success + total_failure) if (total_success + total_failure) > 0 else 1.0
            
            return {
                "success_rate": success_rate,
                "total_rollbacks": total_rollback,
                "total_rejects": total_reject,
                "offending_strategies": [m.strategy_name for m in memories if m.trust_score < 0.3],
                "trusted_strategies": [m.strategy_name for m in memories if m.state == "trusted"]
            }

    @staticmethod
    async def get_adaptation_signals(component: str, family: str) -> Dict[str, Any]:
        """PatchRanker ve Policy Engine için sinyal üretir."""
        async with get_db_ctx() as db:
            res = await db.execute(
                select(StrategyMemory).where(
                    StrategyMemory.component == component,
                    StrategyMemory.error_family == family
                )
            )
            memories = res.scalars().all()
            
            # Query negative patterns for this component/family
            res_neg = await db.execute(
                select(NegativePatternMemory).where(
                    NegativePatternMemory.component == component
                )
            )
            negatives = res_neg.scalars().all()
            
            return {
                "trusted_strategies": [m.strategy_name for m in memories if m.state in ("trusted", "promoted")],
                "risk_scores": {m.strategy_name: (1.0 - m.trust_score) for m in memories},
                "penalty_strategies": {n.strategy_name: n.penalty_weight for n in negatives}
            }
