import asyncio
import sys
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, delete

sys.path.insert(0, '.')
from libs.db.session import async_session_factory, init_db
from libs.db.models.core_models import (
    Project, ProjectStatus, FleetStatus, AgentStatus, AgentRole,
    FleetCluster, AgentNode, FleetAssignment, WorkflowEvent
)
from libs.db.models.auth_models import Operator

async def seed_fleet():
    await init_db()
    async with async_session_factory() as db:
        # Clear existing data for a clean state
        await db.execute(delete(WorkflowEvent))
        await db.execute(delete(FleetAssignment))
        await db.execute(delete(AgentNode))
        await db.execute(delete(FleetCluster))
        await db.execute(delete(Project))
        await db.commit()

        # 1. Seed Operator (if not exists)
        op_res = await db.execute(select(Operator).where(Operator.email == "admin@sovereign.agi"))
        op = op_res.scalars().first()
        if not op:
            op = Operator(
                id=uuid.uuid4(),
                email="admin@sovereign.agi",
                username="admin",
                hashed_password="scrypt:32768:8:1$uH3nU4$e8e9e...", 
                role="MASTER_ADMIN"
            )
            db.add(op)
            await db.flush()

        # 2. Seed Clusters
        c1 = FleetCluster(
            id=uuid.uuid4(),
            name="Main Intel Cluster",
            status=FleetStatus.ACTIVE,
            region="US-EAST",
            budget_limit=5000.0,
            current_budget_usage=120.5,
            max_parallel_projects=10
        )
        c2 = FleetCluster(
            id=uuid.uuid4(),
            name="Edge Processing Node",
            status=FleetStatus.DEGRADED,
            region="EU-WEST",
            budget_limit=1000.0,
            current_budget_usage=850.0,
            max_parallel_projects=3
        )
        db.add_all([c1, c2])
        await db.flush()

        # 3. Seed Agents
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
            name="Beta-Executor-01",
            role=AgentRole.EXECUTOR,
            status=AgentStatus.BUSY,
            trust_score=0.95,
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

        # 4. Seed Projects
        p1 = Project(
            id=uuid.uuid4(),
            owner_id=op.id,
            title="Sovereign Core Upgrade",
            status=ProjectStatus.RUNNING,
            progress_pct=45,
            created_at=datetime.now(timezone.utc) - timedelta(days=1)
        )
        p2 = Project(
            id=uuid.uuid4(),
            owner_id=op.id,
            title="Data Extraction Pipeline",
            status=ProjectStatus.QUEUED,
            progress_pct=0,
            created_at=datetime.now(timezone.utc)
        )
        db.add_all([p1, p2])
        await db.flush()

        # 5. Seed Assignments
        as1 = FleetAssignment(
            id=uuid.uuid4(),
            project_id=p1.id,
            agent_id=a2.id,
            assignment_type="primary",
            status="active",
            started_at=datetime.now(timezone.utc) - timedelta(hours=5)
        )
        db.add(as1)

        # 6. Seed Workflow Events (Governance Proof Records)
        from libs.db.models.governance_models import GovernanceProofEventRecord, ProofEventType, GovernorDomain
        import hashlib

        def quick_hash(text: str) -> str:
            return hashlib.sha256(text.encode()).hexdigest()

        events_to_seed = [
            (ProofEventType.AGENT_ASSIGNED, str(a1.id), f'{{"details": "Agent {a1.name} assigned to Main Intel Cluster"}}', 1),
            (ProofEventType.BUDGET_BLOCK, str(c2.id), '{"details": "Budget limit reached for Edge Processing Node. Automatic scaling blocked."}', 2),
            (ProofEventType.AGENT_QUARANTINED, str(a3.id), f'{{"details": "Agent {a3.name} quarantined due to low trust score (0.45)"}}', 3),
            (ProofEventType.CLUSTER_FROZEN, str(c2.id), '{"details": "Edge Processing Node frozen by Governor due to critical budget breach."}', 4),
        ]

        for etype, eid, payload, idx in events_to_seed:
            phash = quick_hash(payload)
            ehash = quick_hash(f"{phash}{idx}")
            
            evt = GovernanceProofEventRecord(
                id=uuid.uuid4(),
                event_type=etype,
                domain=GovernorDomain.WORKFLOW,
                entity_id=eid,
                payload_hash=phash,
                payload_canonical=payload,
                event_hash=ehash,
                chain_index=idx,
                created_at=datetime.now(timezone.utc) - timedelta(minutes=idx * 10)
            )
            db.add(evt)

        await db.commit()
        print("Successfully seeded clean Fleet data with Events.")

if __name__ == "__main__":
    asyncio.run(seed_fleet())
