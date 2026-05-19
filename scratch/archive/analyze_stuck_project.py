import sys
import os
import io
import asyncio
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.append(os.getcwd())

from libs.db.session import AsyncSessionLocal
from sqlalchemy import text

async def analyze_project(p_id):
    async with AsyncSessionLocal() as db:
        print(f"--- Analyzing Project: {p_id} ---")
        st_query = text("SELECT agent_id, status, result, internal_monologue FROM subtasks WHERE project_id = :p_id")
        st_results = await db.execute(st_query, {"p_id": p_id})
        for st in st_results.fetchall():
            print(f"Agent: {st.agent_id} | Status: {st.status}")
            print(f"Monologue: {st.internal_monologue}")
            print(f"Result: {st.result}")
            print("-" * 20)

if __name__ == "__main__":
    asyncio.run(analyze_project("dfc7b6b45e2c43f09c406e1deada4b6e"))
    # Also run for the latest stabilization fail
    asyncio.run(analyze_project("2752d28a8bc54c369ec475ae4afa7add"))
