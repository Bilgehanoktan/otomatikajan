import asyncio
import sys
import os

sys.path.append('e:/ai_company_faz12.1')

from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import Project, OperationalIncident
from sqlalchemy import select

async def main():
    target_id = "4cb93bf0-8388-4b76-b1e2-e27b4510d847"
    async with AsyncSessionLocal() as db:
        # Check Project details
        res = await db.execute(select(Project).where(Project.id == target_id))
        proj = res.scalar_one_or_none()
        if proj:
            print("=== PROJECT DETAILS ===")
            print(f"ID: {proj.id}")
            print(f"Title: {proj.title}")
            print(f"Status: {proj.status}")
            print(f"Description: {proj.description}")
            print(f"Created At: {proj.created_at}")
            print(f"Updated At: {proj.updated_at}")
            
            # Print all attributes dynamically to see what columns exist
            columns = [c.key for c in proj.__table__.columns]
            print("\nColumns and values:")
            for col in columns:
                print(f"  {col}: {getattr(proj, col)}")
        else:
            print(f"Project with ID {target_id} not found in database.")

        # Check any incidents or related logs
        inc_res = await db.execute(select(OperationalIncident).where(OperationalIncident.project_id == target_id))
        incidents = inc_res.scalars().all()
        if incidents:
            print("\n=== RELATED INCIDENTS ===")
            for inc in incidents:
                print(f"ID: {inc.id}")
                print(f"Incident ID: {inc.incident_id}")
                print(f"Status: {inc.status}")
                print(f"Created At: {inc.created_at}")
                
                # Print all columns of incident
                inc_cols = [c.key for c in inc.__table__.columns]
                print("  Columns:")
                for col in inc_cols:
                    print(f"    {col}: {getattr(inc, col)}")
        else:
            print("\nNo related incidents found.")

if __name__ == "__main__":
    asyncio.run(main())
