
import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import delete, select, text
from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import (
    Project, ProjectStatus, ProjectSource, TaskPriority,
    AgentNode, AgentStatus, AgentRole, FleetCluster, FleetStatus, FleetAssignment,
    WorkflowEvent, SubTask, ApprovalRequest, OperationalIncident, SystemImprovement
)
from libs.db.models.auth_models import Operator, SystemIdentity
from libs.db.models.governance_models import GovernanceProofEventRecord, ProofEventType, GovernorDomain, ValidationResult, ValidationType, ValidationStatus
from libs.db.models.learning_models import LearningRecord, ErrorFingerprint, StrategyMemory

async def seed_fleet():
    print("Starting Comprehensive System Seeding...")
    async with AsyncSessionLocal() as db:
        # Disable foreign keys temporarily for clean delete/reseed
        dialect_name = db.bind.dialect.name
        if dialect_name == "sqlite":
            await db.execute(text("PRAGMA foreign_keys = OFF;"))
        elif dialect_name == "postgresql":
            await db.execute(text("SET session_replication_role = 'replica';"))
        
        
        # 1. Clean existing data (except Operators)
        await db.execute(delete(WorkflowEvent))
        await db.execute(delete(FleetAssignment))
        await db.execute(delete(AgentNode))
        await db.execute(delete(FleetCluster))
        await db.execute(delete(ApprovalRequest))
        await db.execute(delete(OperationalIncident))
        await db.execute(delete(SystemImprovement))
        await db.execute(delete(ValidationResult))
        await db.execute(delete(SubTask))
        await db.execute(delete(Project))
        await db.execute(delete(LearningRecord))
        
        # 2. Ensure Admin Operator
        res = await db.execute(select(Operator).where(Operator.email == "admin@sovereign.agi"))
        op = res.scalar_one_or_none()
        if not op:
            op = Operator(
                id=uuid.UUID("a394ea7a-943d-4f67-97aa-fa53984040d7"), # Fixed ID for stability
                email="admin@sovereign.agi",
                hashed_password="$2b$12$sRKqRyvDPfq2qURdhkEPlemrTzVJwRzhfOQx51BBZ51nqSH1W0jo.", # "admin123"
                role="SOVEREIGN_PRIME",
                is_active=True
            )
            db.add(op)
        else:
            op.role = "SOVEREIGN_PRIME" # Ensure correct role
            
        await db.flush()

        # 3. Seed Clusters
        c1 = FleetCluster(
            id=uuid.uuid4(),
            name="Main Intel Cluster",
            region="eu-central-1",
            status=FleetStatus.ACTIVE,
            budget_limit=500.0,
            max_parallel_projects=10
        )
        c2 = FleetCluster(
            id=uuid.uuid4(),
            name="Edge Processing Node",
            region="us-east-1",
            status=FleetStatus.DEGRADED,
            budget_limit=200.0,
            max_parallel_projects=5
        )
        db.add_all([c1, c2])
        await db.flush()

        # 4. Seed Agents
        a1 = AgentNode(
            id=uuid.uuid4(),
            cluster_id=c1.id,
            name="Alpha-Planner-01",
            role=AgentRole.PLANNER,
            status=AgentStatus.IDLE,
            trust_score=0.98,
            current_load=0,
            max_concurrency=2
        )
        a2 = AgentNode(
            id=uuid.uuid4(),
            cluster_id=c1.id,
            name="Beta-Executor-05",
            role=AgentRole.EXECUTOR,
            status=AgentStatus.BUSY,
            trust_score=0.92,
            current_load=1,
            max_concurrency=1
        )
        a3 = AgentNode(
            id=uuid.uuid4(),
            cluster_id=c2.id,
            name="Gamma-Reviewer-01",
            role=AgentRole.REVIEWER,
            status=AgentStatus.QUARANTINED,
            trust_score=0.45,
            current_load=0,
            max_concurrency=1
        )
        db.add_all([a1, a2, a3])
        await db.flush()

        # 5. Seed Projects & SubTasks
        p1 = Project(
            id=uuid.uuid4(),
            owner_id=op.id,
            title="Sovereign Core Upgrade",
            status=ProjectStatus.RUNNING,
            progress_pct=45,
            created_at=datetime.now(timezone.utc) - timedelta(days=1),
            source=ProjectSource.CONTROL_PLANE,
            priority=TaskPriority.HIGH
        )
        p2 = Project(
            id=uuid.uuid4(),
            owner_id=op.id,
            title="Data Extraction Pipeline",
            status=ProjectStatus.QUEUED,
            progress_pct=0,
            created_at=datetime.now(timezone.utc),
            source=ProjectSource.API,
            priority=TaskPriority.MEDIUM
        )
        db.add_all([p1, p2])
        await db.flush()

        # Seed SubTasks for P1 to show in Workflow view
        st1 = SubTask(
            id=uuid.uuid4(),
            project_id=p1.id,
            agent_id=str(a1.id),
            action="Plan Architecture",
            prompt="Analyze core components for upgrade.",
            status=ProjectStatus.COMPLETED,
            result="Architecture plan finalized.",
            created_at=datetime.now(timezone.utc) - timedelta(hours=5)
        )
        st2 = SubTask(
            id=uuid.uuid4(),
            project_id=p1.id,
            agent_id=str(a2.id),
            action="Implement Security Layer",
            prompt="Apply SIF-01 identity framework.",
            status=ProjectStatus.RUNNING,
            result="Deployment in progress...",
            created_at=datetime.now(timezone.utc) - timedelta(hours=2)
        )
        db.add_all([st1, st2])

        # 6. Seed Workflow Events (Timeline)
        ev1 = WorkflowEvent(
            id=uuid.uuid4(),
            project_id=p1.id,
            event_type="workflow_started",
            operator_id="system",
            payload={"message": "System initiated Sovereign Core Upgrade"},
            created_at=datetime.now(timezone.utc) - timedelta(hours=6)
        )
        ev2 = WorkflowEvent(
            id=uuid.uuid4(),
            project_id=p1.id,
            event_type="step_completed",
            step_id=str(st1.id),
            operator_id=str(a1.id),
            payload={"result": "Plan approved by Governor"},
            created_at=datetime.now(timezone.utc) - timedelta(hours=4)
        )
        db.add_all([ev1, ev2])

        # 7. Seed Approval Requests (Governor Inbox)
        app1 = ApprovalRequest(
            id=uuid.uuid4(),
            project_id=p1.id,
            request_type="autonomy_elevation",
            reason="Project requires direct filesystem access for patch application.",
            status="pending",
            created_at=datetime.now(timezone.utc) - timedelta(minutes=30)
        )
        app2 = ApprovalRequest(
            id=uuid.uuid4(),
            project_id=p2.id,
            request_type="budget_increase",
            reason="Large dataset detected, requires additional compute resources.",
            status="pending",
            created_at=datetime.now(timezone.utc) - timedelta(minutes=15)
        )
        db.add_all([app1, app2])

        # 8. Seed Operational Incidents
        inc1 = OperationalIncident(
            id=uuid.uuid4(),
            incident_type="stuck_workflow",
            severity="high",
            message="Beta-Executor-05 is unresponsive in Main Intel Cluster.",
            status="open",
            project_id=p1.id,
            created_at=datetime.now(timezone.utc) - timedelta(hours=1)
        )
        db.add(inc1)

        # 9. Seed Simulation Results (Training Hub)
        val1 = ValidationResult(
            id=uuid.uuid4(),
            component_name="SIF-01-Auth",
            validation_type=ValidationType.CONTINUOUS,
            status=ValidationStatus.PASS,
            metrics={"latency_avg": 45.2, "success_rate": 0.998},
            created_at=datetime.now(timezone.utc) - timedelta(hours=12)
        )
        val2 = ValidationResult(
            id=uuid.uuid4(),
            component_name="Fleet-Orchestrator",
            validation_type=ValidationType.DRILL,
            status=ValidationStatus.WARN,
            metrics={"rebalance_efficiency": 0.65},
            error_log="Slow response from Edge Node during simulated failover.",
            created_at=datetime.now(timezone.utc) - timedelta(hours=24)
        )
        db.add_all([val1, val2])

        # 10. Seed Learning Records (Otonom Hafıza)
        learn1 = LearningRecord(
            id=uuid.uuid4(),
            project_id=p1.id,
            root_cause="Missing foreign key constraint in legacy schema.",
            proposed_fix_type="code",
            strategy_used="Automated Migration Generator",
            final_outcome="SUCCESS",
            verification_score=0.95,
            created_at=datetime.now(timezone.utc) - timedelta(days=2)
        )
        db.add(learn1)

        # 11. Seed System Improvements (Evolution Dashboard)
        imp1 = SystemImprovement(
            id=uuid.uuid4(),
            target_file="libs/db/session.py",
            instruction="Implement automated foreign key constraint validation loop.",
            proposed_patch="--- libs/db/session.py\n+++ libs/db/session.py\n@@ -10,1 +10,1 @@\n-    pass\n+    validate_constraints()",
            status="applied",
            risk_score=0.1,
            created_at=datetime.now(timezone.utc) - timedelta(days=1)
        )
        imp2 = SystemImprovement(
            id=uuid.uuid4(),
            target_file="services/auth/jwt_auth.py",
            instruction="Reduce JWT lifetime to 15m for high-security environments.",
            proposed_patch="--- services/auth/jwt_auth.py\n+++ services/auth/jwt_auth.py\n@@ -32,1 +32,1 @@\n-ACCESS_MINUTES = 1440\n+ACCESS_MINUTES = 15",
            status="pending",
            risk_score=0.4,
            created_at=datetime.now(timezone.utc) - timedelta(hours=5)
        )
        db.add_all([imp1, imp2])

        if dialect_name == "postgresql":
            await db.execute(text("SET session_replication_role = 'origin';"))

        await db.commit()
        print("Successfully seeded all System modules.")

if __name__ == "__main__":
    asyncio.run(seed_fleet())
