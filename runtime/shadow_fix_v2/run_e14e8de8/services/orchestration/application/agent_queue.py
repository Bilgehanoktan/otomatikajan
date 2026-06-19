import asyncio
import heapq
import time
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from sqlalchemy import select, delete
from services.observability.logging import get_logger

# Database & Session
from libs.db.session import session_scope
from apps.bilgeapi.models.database import (
    AgentTaskQueueModel,
    AgentTaskLeaseModel,
    AgentOrchestrationRunModel,
    IncidentModel
)
from apps.bilgeapi.repositories.postgres import PostgresIncidentRepository, PostgresAutonomyDecisionRepository
from apps.bilgeapi.services.autonomy_decision import AutonomyDecisionEngine, AutonomyMode
from apps.bilgeapi.schemas.incident import IncidentCreate, Severity

# AGI Layer
from services.orchestration.agi.governance.consensus_arbiter import consensus_arbiter
from services.orchestration.agi.operational.kinetic_arbiter import kinetic_arbiter
from services.orchestration.agi.consciousness.affective_core import affective_core

_log = get_logger("agent_orchestration_queue")

# Ajan rollerinin ağırlıkları (Daha büyük değer = Daha yüksek öncelik)
ROLE_WEIGHTS = {
    "self_governor": 10.0,
    "security":       9.0,
    "architect":      8.0,
    "deerflow_planner": 7.5,
    "planner":        7.0,
    "strategist":     7.0,
    "backend_dev":    5.0,
    "frontend_dev":   5.0,
    "devops":         5.0,
    "qa_engineer":    4.0,
    "critic":         4.0,
    "researcher":     4.0,
    "tech_writer":    2.0,
    "general":        3.0
}

# Güvenli Eylemler Katalogu (Sadece bunlar AUTO_RUN olabilir)
SAFE_ACTIONS = [
    "clear_local_cache",
    "health_recheck",
    "read-only_diagnostic",
    "stuck_job_cancel",
    "refresh_registry_cache",
    "collect_logs",
    "generate_evidence"
]

@dataclass
class QueueTask:
    priority: float  # Negatif priority_score (küçük olan heapq'da önce çıkar)
    timestamp: float
    task_id: str

    def __lt__(self, other: "QueueTask") -> bool:
        if abs(self.priority - other.priority) > 1e-9:
            return self.priority < other.priority
        return self.timestamp < other.timestamp


def _normalize_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class AgentOrchestrationQueue:
    """
    Kalıcı ve Karar Geçitli Ajan İş Kuyruğu (Persistent & Gated Agent Queue).
    """

    def calculate_priority(
        self,
        role: str,
        urgency: float,
        stress: float,
        risk_level: str,
        attempt_count: int
    ) -> float:
        """
        Bilişsel Önceliklendirme Formülü:
        priority_score = role_weight + urgency_weight + risk_weight - stress_penalty - retry_penalty
        """
        role_weight = ROLE_WEIGHTS.get(role, 3.0)
        urgency_weight = urgency * 5.0
        
        # Risk seviyesi ağırlığı
        risk_weight = {
            "low": 1.0,
            "medium": 3.0,
            "high": 5.0,
            "critical": 10.0
        }.get(risk_level.lower(), 1.0)
        
        stress_penalty = stress * 3.0
        retry_penalty = attempt_count * 2.0
        
        priority_score = role_weight + urgency_weight + risk_weight - stress_penalty - retry_penalty
        return priority_score

    async def enqueue(
        self,
        task_id: str,
        source: str,
        agent_role: str,
        action_type: str,
        payload: Optional[Dict[str, Any]] = None,
        risk_level: str = "low",
        urgency: float = 0.5,
        stress: float = 0.2,
        idempotency_key: Optional[str] = None,
        max_attempts: int = 3
    ) -> Dict[str, Any]:
        """
        Görevi veritabanı kuyruğuna ekler. Idempotency kontrolü yapar.
        """
        async with session_scope() as db:
            if idempotency_key:
                stmt = select(AgentTaskQueueModel).where(AgentTaskQueueModel.idempotency_key == idempotency_key)
                res = await db.execute(stmt)
                existing = res.scalar_one_or_none()
                if existing:
                    _log.info(f"[QUEUE] Idempotency key match found. Skipping task duplicate: {idempotency_key}")
                    return self._task_to_dict(existing)

            priority_score = self.calculate_priority(
                role=agent_role,
                urgency=urgency,
                stress=stress,
                risk_level=risk_level,
                attempt_count=0
            )

            task = AgentTaskQueueModel(
                task_id=task_id,
                source=source,
                agent_role=agent_role,
                action_type=action_type,
                payload=payload,
                risk_level=risk_level.lower(),
                priority_score=priority_score,
                status="PENDING",
                idempotency_key=idempotency_key,
                attempt_count=0,
                max_attempts=max_attempts
            )
            db.add(task)
            await db.commit()
            await db.refresh(task)
            _log.info(f"[QUEUE] Task enqueued: {task_id} (Priority Score: {priority_score:.2f})")
            return self._task_to_dict(task)

    async def process_next(self, context: str = "agent_queue") -> Optional[Dict[str, Any]]:
        """
        Kuyruktan en öncelikli görevi çeker, kilitler (lease), karar motorundan onay alır ve çalıştırır.
        """
        async with session_scope() as db:
            now = datetime.now(timezone.utc)
            
            # 1. Eligible görevleri seç
            stmt = (
                select(AgentTaskQueueModel, AgentTaskLeaseModel)
                .outerjoin(AgentTaskLeaseModel, AgentTaskQueueModel.task_id == AgentTaskLeaseModel.task_id)
                .where(
                    (AgentTaskQueueModel.status.in_(["PENDING", "RETRY_SCHEDULED"])) |
                    ((AgentTaskQueueModel.status == "LEASED") & (AgentTaskLeaseModel.lease_expires_at < now))
                )
            )
            res = await db.execute(stmt)
            rows = res.all()
            if not rows:
                return None

            # 2. Bilişsel öncelik sıralaması (heapq)
            aff_state = affective_core.get_state_matrix() if hasattr(affective_core, "get_state_matrix") else {}
            urgency = aff_state.get("urgency", 0.5)
            stress = aff_state.get("internal_stress", 0.2)

            heap = []
            for task_model, lease_model in rows:
                prio_score = self.calculate_priority(
                    role=task_model.agent_role,
                    urgency=urgency,
                    stress=stress,
                    risk_level=task_model.risk_level,
                    attempt_count=task_model.attempt_count
                )
                ts = task_model.created_at.timestamp()
                heapq.heappush(heap, QueueTask(priority=-prio_score, timestamp=ts, task_id=task_model.task_id))

            # 3. Sıradaki görevi seçip kilitlemeye (lease) çalış
            leased_task = None
            while heap:
                q_task = heapq.heappop(heap)
                task_id = q_task.task_id

                # select_for_update ile satır kilitle
                task_stmt = select(AgentTaskQueueModel).where(AgentTaskQueueModel.task_id == task_id).with_for_update()
                task_res = await db.execute(task_stmt)
                task_model = task_res.scalar_one_or_none()

                if not task_model:
                    continue

                if task_model.status == "LEASED":
                    lease_stmt = select(AgentTaskLeaseModel).where(AgentTaskLeaseModel.task_id == task_id)
                    lease_res = await db.execute(lease_stmt)
                    lease_model = lease_res.scalar_one_or_none()
                    if not lease_model or _normalize_utc(lease_model.lease_expires_at) >= _normalize_utc(now):
                        continue
                elif task_model.status not in ["PENDING", "RETRY_SCHEDULED"]:
                    continue

                # Kilitle (lease)
                task_model.status = "LEASED"
                task_model.attempt_count += 1
                task_model.updated_at = now

                lease_expires = now + timedelta(seconds=30)
                lease_stmt = select(AgentTaskLeaseModel).where(AgentTaskLeaseModel.task_id == task_id)
                lease_res = await db.execute(lease_stmt)
                existing_lease = lease_res.scalar_one_or_none()

                if existing_lease:
                    existing_lease.lease_owner = context
                    existing_lease.lease_expires_at = lease_expires
                    existing_lease.acquired_at = now
                else:
                    new_lease = AgentTaskLeaseModel(
                        task_id=task_id,
                        lease_owner=context,
                        lease_expires_at=lease_expires,
                        acquired_at=now
                    )
                    db.add(new_lease)

                await db.commit()
                await db.refresh(task_model)
                leased_task = task_model
                break

            if not leased_task:
                return None

            # 4. Deneme limiti aşımı kontrolü (DEAD_LETTER)
            if leased_task.attempt_count > leased_task.max_attempts:
                leased_task.status = "DEAD_LETTER"
                leased_task.updated_at = datetime.now(timezone.utc)
                
                run = AgentOrchestrationRunModel(
                    task_id=leased_task.task_id,
                    status="FAILED",
                    execution_summary=f"Max attempts ({leased_task.max_attempts}) exceeded.",
                    started_at=now,
                    completed_at=datetime.now(timezone.utc)
                )
                db.add(run)
                # Kilidi kaldır
                await db.execute(delete(AgentTaskLeaseModel).where(AgentTaskLeaseModel.task_id == leased_task.task_id))
                await db.commit()
                _log.warning(f"[QUEUE] Task {leased_task.task_id} marked as DEAD_LETTER (Max attempts exceeded).")
                return self._task_to_dict(leased_task)

            # 5. AutonomyDecisionEngine için dummy incident oluştur
            incident_id = f"inc-task-{leased_task.task_id}"
            sev_val = leased_task.risk_level.upper()
            if sev_val not in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
                sev_val = "LOW"
            severity = Severity(sev_val)

            incident_model = IncidentModel(
                id=incident_id,
                project_key="default",
                source_system=leased_task.source,
                environment="production" if leased_task.source.lower() == "production" else "development",
                kind=leased_task.action_type,
                severity=severity.value,
                error_message=f"Queue proposed action: {leased_task.action_type}",
                occurred_at=now,
                correlation_id=leased_task.task_id,
                tags=["orchestration", leased_task.agent_role],
                metadata_fields=leased_task.payload or {}
            )
            await db.merge(incident_model)
            await db.commit()

            # 6. AutonomyDecisionEngine ile kararı al
            incident_repo = PostgresIncidentRepository(db)
            decision_repo = PostgresAutonomyDecisionRepository(db)
            decision_engine = AutonomyDecisionEngine(decision_repo=decision_repo, incident_repo=incident_repo)

            decision = await decision_engine.decide(incident_id=incident_id, action_type=leased_task.action_type)
            eligibility = decision["eligibility"]

            # Karar kimliğini göreve bağla
            leased_task.decision_id = decision["decision_id"]
            leased_task.updated_at = datetime.now(timezone.utc)
            await db.commit()

            _log.info(f"[QUEUE] Autonomy Decision for task {leased_task.task_id}: {eligibility}")

            # 7. Yüksek/Orta riskli görevler için ConsensusArbiter Entegrasyonu
            # Veto durumlarının kontrolü
            if leased_task.risk_level in ["medium", "high", "critical"]:
                from services.orchestration.agi.task_governance import GovernedTask, GovernanceStatus
                gt = GovernedTask(
                    id=leased_task.task_id,
                    agent_id=leased_task.agent_role,
                    prompt=f"Task action: {leased_task.action_type}. Payload: {leased_task.payload}",
                    risk_level=leased_task.risk_level,
                    status=GovernanceStatus.RUNNING
                )
                debate_ok, debate_report = await consensus_arbiter.execute_debate(gt, context=context)
                if not debate_ok:
                    leased_task.status = "BLOCKED_CONSENSUS_VETO"
                    run = AgentOrchestrationRunModel(
                        task_id=leased_task.task_id,
                        status="FAILED",
                        execution_summary=f"Consensus Veto: {debate_report.get('error', 'Debate did not reach consensus.')}",
                        started_at=now,
                        completed_at=datetime.now(timezone.utc)
                    )
                    db.add(run)
                    await db.execute(delete(AgentTaskLeaseModel).where(AgentTaskLeaseModel.task_id == leased_task.task_id))
                    await db.commit()
                    return self._task_to_dict(leased_task)

            # 8. Karara ve risk seviyesine göre durum güncellemesi
            if eligibility == "BLOCKED" or leased_task.risk_level == "critical":
                leased_task.status = "BLOCKED"
                run = AgentOrchestrationRunModel(
                    task_id=leased_task.task_id,
                    status="BLOCKED",
                    execution_summary=f"Blocked. Reason: {decision['decision_reason']}",
                    started_at=now,
                    completed_at=datetime.now(timezone.utc)
                )
                db.add(run)
                await db.execute(delete(AgentTaskLeaseModel).where(AgentTaskLeaseModel.task_id == leased_task.task_id))
                await db.commit()
                return self._task_to_dict(leased_task)

            elif eligibility in ["HUMAN_GATE_REQUIRED", "WARNING_OPERATOR_REVIEW"] or leased_task.risk_level in ["medium", "high"]:
                leased_task.status = "HUMAN_GATE_REQUIRED"
                run = AgentOrchestrationRunModel(
                    task_id=leased_task.task_id,
                    status="HUMAN_GATE_REQUIRED",
                    execution_summary=f"Requires human approval. Reason: {decision['decision_reason']}",
                    started_at=now,
                    completed_at=datetime.now(timezone.utc)
                )
                db.add(run)
                await db.execute(delete(AgentTaskLeaseModel).where(AgentTaskLeaseModel.task_id == leased_task.task_id))
                await db.commit()
                return self._task_to_dict(leased_task)

            elif eligibility == "AUTO_RUN":
                # Güvenli Eylemler Katalogu kontrolü
                if leased_task.action_type not in SAFE_ACTIONS:
                    _log.warning(f"[QUEUE] Action {leased_task.action_type} is not in Safe Action Catalog. Routing to HUMAN_GATE_REQUIRED.")
                    leased_task.status = "HUMAN_GATE_REQUIRED"
                    run = AgentOrchestrationRunModel(
                        task_id=leased_task.task_id,
                        status="HUMAN_GATE_REQUIRED",
                        execution_summary="Auto-run declined: Action type is not in the Safe Action Catalog.",
                        started_at=now,
                        completed_at=datetime.now(timezone.utc)
                    )
                    db.add(run)
                    await db.execute(delete(AgentTaskLeaseModel).where(AgentTaskLeaseModel.task_id == leased_task.task_id))
                    await db.commit()
                    return self._task_to_dict(leased_task)

                # 9. Pacing (KineticArbiter Entegrasyonu)
                await kinetic_arbiter.acquire_slot(leased_task.agent_role, leased_task.task_id)
                try:
                    leased_task.status = "RUNNING"
                    run = AgentOrchestrationRunModel(
                        task_id=leased_task.task_id,
                        status="RUNNING",
                        started_at=now
                    )
                    db.add(run)
                    await db.commit()

                    # Otonom safe action simülasyonu
                    await asyncio.sleep(0.1)

                    leased_task.status = "COMPLETED"
                    run.status = "COMPLETED"
                    run.execution_summary = f"Successfully executed safe action: {leased_task.action_type}"
                    run.completed_at = datetime.now(timezone.utc)
                    await db.commit()

                finally:
                    kinetic_arbiter.release_slot()
                    await db.execute(delete(AgentTaskLeaseModel).where(AgentTaskLeaseModel.task_id == leased_task.task_id))
                    await db.commit()

                await db.refresh(leased_task)
                return self._task_to_dict(leased_task)

            else:
                leased_task.status = "BLOCKED"
                await db.execute(delete(AgentTaskLeaseModel).where(AgentTaskLeaseModel.task_id == leased_task.task_id))
                await db.commit()
                return self._task_to_dict(leased_task)

    def _task_to_dict(self, task: AgentTaskQueueModel) -> Dict[str, Any]:
        return {
            "task_id": task.task_id,
            "source": task.source,
            "agent_role": task.agent_role,
            "action_type": task.action_type,
            "payload": task.payload,
            "risk_level": task.risk_level,
            "priority_score": task.priority_score,
            "status": task.status,
            "idempotency_key": task.idempotency_key,
            "attempt_count": task.attempt_count,
            "max_attempts": task.max_attempts,
            "decision_id": task.decision_id,
            "created_at": task.created_at,
            "updated_at": task.updated_at
        }
