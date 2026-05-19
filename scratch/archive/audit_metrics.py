
import asyncio
import os
import sys

# Add project root to sys.path
sys.path.append(os.getcwd())

from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import Project, SubTask, OperationalIncident
from sqlalchemy import select, func

async def get_metrics():
    print("--- SOVEREIGN AUDIT METRICS ---")
    async with AsyncSessionLocal() as session:
        # 1. Project Info
        p_res = await session.execute(select(Project).where(Project.is_pilot == True))
        project = p_res.scalars().first()
        if project:
            print(f"Pilot Project: {project.title}")
            print(f"Status: {project.status}")
            print(f"Budget: ${project.budget_limit}")
            print(f"Burn Rate: ${project.hourly_burn_rate}/h")
        else:
            print("Pilot Project: NOT FOUND")

        # 2. SubTask Counts
        st_res = await session.execute(
            select(
                func.count(SubTask.id).label("total"),
                func.count(SubTask.id).filter(SubTask.status == "COMPLETED").label("completed"),
                func.count(SubTask.id).filter(SubTask.status == "RUNNING").label("running")
            ).where(SubTask.project_id == project.id if project else True)
        )
        row = st_res.one()
        print(f"SubTasks: Total={row.total}, Completed={row.completed}, Running={row.running}")

        # 3. Incident Info
        inc_res = await session.execute(select(func.count(OperationalIncident.id)))
        print(f"Total Incidents: {inc_res.scalar()}")

        # 4. Latency
        lat_res = await session.execute(select(func.avg(SubTask.latency_s)).filter(SubTask.status == "COMPLETED"))
        avg_lat = lat_res.scalar() or 0
        print(f"Average Approval Latency: {avg_lat:.2f}s")
    print("--- END AUDIT ---")

if __name__ == "__main__":
    asyncio.run(get_metrics())
