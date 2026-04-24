
import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from libs.db.session import get_db_ctx, init_db
from libs.db.models.core_models import Project, TaskLog, ProjectStatus, ProjectSource, TaskPriority
from sqlalchemy import select

async def seed_workflows():
    print("=== Seeding Workflows (Projects) & Task Logs ===")
    await init_db()
    
    async with get_db_ctx() as db:
        # 1. Active Workflow
        project_id = uuid.uuid4()
        p1 = Project(
            id=project_id,
            title="Final Durum Taraması (V5) - Hardening Check",
            description="Operational audit of the core resilience layers after Phase 31 deployment.",
            status=ProjectStatus.RUNNING,
            source=ProjectSource.CONTROL_PLANE,
            priority=TaskPriority.CRITICAL,
            progress_pct=65,
            created_at=datetime.now(timezone.utc) - timedelta(hours=1),
            started_at=datetime.now(timezone.utc) - timedelta(minutes=45)
        )
        db.add(p1)
        
        # 2. Add logs for P1
        logs = [
            TaskLog(project_id=project_id, event="workflow_started", message="Workflow initialized by Egemen YAZ", level="info"),
            TaskLog(project_id=project_id, event="agent_start", message="Resilience Auditor started analysis", agent_id="auditor-01"),
            TaskLog(project_id=project_id, event="agent_done", message="Phase 1: Connectivity check passed", agent_id="auditor-01"),
            TaskLog(project_id=project_id, event="status_change", message="Transitioning to step: Governance Validation", level="info")
        ]
        for log in logs:
            db.add(log)
            
        # 3. Pending Approval Workflow
        p2_id = uuid.uuid4()
        p2 = Project(
            id=p2_id,
            title="Sovereign Federation Bridge - Port 8010",
            description="Establishment of the P2P Mesh Bridge for cross-cluster learning synchronization.",
            status=ProjectStatus.PENDING_APPROVAL,
            source=ProjectSource.API,
            priority=TaskPriority.HIGH,
            progress_pct=10,
            created_at=datetime.now(timezone.utc) - timedelta(minutes=20)
        )
        db.add(p2)
        
        db.add(TaskLog(project_id=p2_id, event="waiting_approval", message="Autonomy level requires manual sign-off for Federation Bridge deployment.", level="warning"))

        # 4. Completed Workflow
        p3_id = uuid.uuid4()
        p3 = Project(
            id=p3_id,
            title="SQLite Resilience Armor Patch",
            description="Hot-patch for SQLite fallback mechanism persistence stability.",
            status=ProjectStatus.COMPLETED,
            source=ProjectSource.CONTROL_PLANE,
            priority=TaskPriority.MEDIUM,
            progress_pct=100,
            created_at=datetime.now(timezone.utc) - timedelta(days=1),
            completed_at=datetime.now(timezone.utc) - timedelta(days=1, hours=22)
        )
        db.add(p3)

        await db.commit()
        print("Workflows and TaskLogs seeded successfully.")

if __name__ == "__main__":
    asyncio.run(seed_workflows())
