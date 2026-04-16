import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, update
from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import User, Project, OperationalIncident, SystemImprovement, ProjectStatus, SubTask

async def bootstrap():
    print("🚀 Starting Sovereign AGI Pilot Bootstrap...")
    async with AsyncSessionLocal() as session:
        # 1. Create Default Admin User
        result = await session.execute(select(User).filter_by(email="admin@sovereign.agi"))
        user = result.scalars().first()
        if not user:
            print("Creating default admin user...")
            user = User(
                id=uuid.uuid4(),
                email="admin@sovereign.agi",
                hashed_password="[PROTECTED]", # Mock password
                is_admin=True
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        else:
            print(f"Admin user already exists: {user.id}")

        # 2. Create Resilience Pilot Project
        result = await session.execute(select(Project).filter_by(title="Resilience Pilot v1"))
        project = result.scalars().first()
        if not project:
            print("Creating Resilience Pilot Project...")
            project = Project(
                id=uuid.uuid4(),
                owner_id=user.id,
                title="Resilience Pilot v1",
                description="Phase 16 Autonomous Self-Correction & Reliability Pilot",
                status=ProjectStatus.RUNNING,
                is_pilot=True,
                budget_limit=100.0,
                workflow_template="resilience_v1",
                # Phase 23: Isolation & Autonomy
                isolation_tier=1, # Production Tier
                autonomy_envelope={
                    "mode": "autonomous",
                    "allow_auto_patch": True,
                    "max_risk_score": 0.5,
                    "isolation_zone": "eu-central-1"
                },
                concurrency_limit=10,
                # Phase 24: Economics
                current_budget_usd=100.0,
                hourly_burn_rate=2.5,
                economic_profile={
                    "steering_policy": "performance_optimized",
                    "min_budget_threshold": 20.0,
                    "auto_scale_concurrency": True
                }
            )
            session.add(project)
            await session.commit()
            await session.refresh(project)
        else:
            print(f"Pilot project already exists: {project.id}")

        # 3. Link existing incidents to the project
        print("Linking orphan incidents to pilot project...")
        stmt = update(OperationalIncident).where(
            OperationalIncident.project_id == None
        ).values(project_id=project.id)
        await session.execute(stmt)

        # 4. Generate some sample improvement history
        print("Seeding improvement history...")
        # A. An applied patch (The ConnectionManager fix)
        applied_patch = SystemImprovement(
            id=uuid.uuid4(),
            target_file="libs/infra/ws_manager.py",
            instruction="Add client_count property to ConnectionManager to resolve attribute errors in health checks.",
            proposed_patch="+    @property\n+    def client_count(self) -> int:\n+        return len(self.active_connections)",
            status="applied",
            applied_at=datetime.now(timezone.utc) - timedelta(hours=2),
            risk_score=0.1
        )
        session.add(applied_patch)

        # B. A rolled back patch (Simulation of safety gate working)
        rollback_patch = SystemImprovement(
            id=uuid.uuid4(),
            target_file="libs/db/session.py",
            instruction="Unsafe pool size increase simulation.",
            proposed_patch="-pool_size=10\n+pool_size=1000",
            status="rolled_back",
            applied_at=datetime.now(timezone.utc) - timedelta(hours=4),
            risk_score=0.85
        )
        session.add(rollback_patch)

        # C. Active Canary (In progress)
        canary_patch = SystemImprovement(
            id=uuid.uuid4(),
            target_file="apps/public_api/main.py",
            instruction="Optimize dashboard routing for faster load times.",
            proposed_patch="Refactored static mount logic.",
            status="canary",
            created_at=datetime.now(timezone.utc) - timedelta(minutes=5),
            risk_score=0.15
        )
        session.add(canary_patch)

        # 5. Mark some incidents as resolved
        print("Resolving linked incidents...")
        inc_stmt = update(OperationalIncident).where(
            OperationalIncident.project_id == project.id
        ).values(status="resolved", resolved_at=datetime.now(timezone.utc))
        await session.execute(inc_stmt)

        # 6. Inject Pilot Workflow sequence (SubTasks)
        print("Injecting Pilot Workflow sequence...")
        subtasks_data = [
            {
                "agent_id": "orchestrator",
                "action": "analyze_incidents",
                "prompt": "Evaluate recent operational incidents for pattern and risk.",
                "status": ProjectStatus.COMPLETED,
                "latency_s": 12.5,
                "completed_at": datetime.now(timezone.utc) - timedelta(minutes=10)
            },
            {
                "agent_id": "architect",
                "action": "propose_improvement",
                "prompt": "Design a systemic fix for the identified vulnerability.",
                "status": ProjectStatus.COMPLETED,
                "latency_s": 45.2,
                "completed_at": datetime.now(timezone.utc) - timedelta(minutes=8)
            },
            {
                "agent_id": "engineer",
                "action": "generate_patch",
                "prompt": "Write the verified patch code for the target vulnerability.",
                "status": ProjectStatus.COMPLETED,
                "latency_s": 32.1,
                "completed_at": datetime.now(timezone.utc) - timedelta(minutes=5)
            },
            {
                "agent_id": "sre",
                "action": "run_canary",
                "prompt": "Deploy patch in canary mode and monitor health for 15m.",
                "status": ProjectStatus.RUNNING,
                "latency_s": 300.0
            },
            {
                "agent_id": "orchestrator",
                "action": "verify_promotion",
                "prompt": "Final verification and promotion to global production.",
                "status": ProjectStatus.PENDING,
                "latency_s": 0.0
            }
        ]
        
        for st_data in subtasks_data:
            session.add(SubTask(
                id=uuid.uuid4(),
                project_id=project.id,
                **st_data
            ))

        await session.commit()
        print("✅ Bootstrap complete! Dashboard should now reflect Phase 16/17 state.")

if __name__ == "__main__":
    asyncio.run(bootstrap())
