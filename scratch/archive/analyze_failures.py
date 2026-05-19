
import asyncio
import sys
import os
sys.path.append(os.getcwd())

from libs.db.session import AsyncSessionLocal
from sqlalchemy import text

async def analyze_failures():
    async with AsyncSessionLocal() as db:
        print("--- Analyzing Last 5 Failed Workflows ---")
        # Querying projects with their latest failure status
        query = text("""
            SELECT id, title, status, last_error 
            FROM projects 
            WHERE status = 'error' OR status = 'failed'
            ORDER BY updated_at DESC LIMIT 5
        """)
        results = await db.execute(query)
        failed_projects = results.fetchall()
        
        for p in failed_projects:
            print(f"Project ID: {p.id}")
            print(f"Title: {p.title}")
            print(f"Status: {p.status}")
            print(f"Error: {p.last_error}")
            
            # Querying subtasks for this project
            st_query = text("SELECT agent_id, status, result FROM subtasks WHERE project_id = :p_id")
            st_results = await db.execute(st_query, {"p_id": p.id})
            for st in st_results.fetchall():
                print(f"  - SubTask [{st.agent_id}]: {st.status}")
                if "error" in str(st.status).lower():
                    print(f"    Result: {st.result[:200]}...")
            print("-" * 30)

if __name__ == "__main__":
    asyncio.run(analyze_failures())
