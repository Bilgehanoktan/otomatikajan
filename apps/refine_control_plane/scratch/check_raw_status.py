import asyncio
import uuid
import sys
import os

# Ensure the project root is in path
sys.path.append('e:/ai_company_faz12.1')

from libs.db.session import AsyncSessionLocal
from sqlalchemy import text

async def check_raw_status(workflow_id):
    try:
        # Check if it's already a UUID object or needs conversion
        uid = workflow_id
        async with AsyncSessionLocal() as db:
            # Check project status
            res = await db.execute(text("SELECT id, status FROM projects WHERE id = :id"), {"id": uid})
            p = res.first()
            if p:
                print(f"Project ID={p[0]}, Raw Status='{p[1]}'")
            else:
                print(f"Project {uid} not found in projects table.")
            
            # Check subtasks status
            res_st = await db.execute(text("SELECT id, agent_id, status FROM subtasks WHERE project_id = :id"), {"id": uid})
            subtasks = res_st.all()
            for st in subtasks:
                print(f"SubTask ID={st[0]}, Agent='{st[1]}', Raw Status='{st[2]}'")
            if not subtasks:
                print(f"No subtasks found for project {uid}.")
                
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    workflow_id = "6bf72fb5-7cd8-4d9e-b928-54af95867c64"
    asyncio.run(check_raw_status(workflow_id))
