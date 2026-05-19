import asyncio
import uuid
import sys
import os

# Ensure the project root is in path
sys.path.append('e:/ai_company_faz12.1')

from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import Project
from sqlalchemy import select

async def check_workflow(workflow_id):
    try:
        uid = uuid.UUID(workflow_id)
        async with AsyncSessionLocal() as db:
            res = await db.execute(select(Project).where(Project.id == uid))
            project = res.scalar_one_or_none()
            if project:
                print(f"FOUND: Project ID={project.id}, Title='{project.title}', Status={project.status}")
                return True
            else:
                print(f"NOT FOUND: Project ID={workflow_id}")
                return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    workflow_id = "6bf72fb5-7cd8-4d9e-b928-54af95867c64"
    asyncio.run(check_workflow(workflow_id))
