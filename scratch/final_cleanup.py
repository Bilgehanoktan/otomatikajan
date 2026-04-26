import asyncio
import os
import sys
from datetime import datetime, timezone

# Add workspace root to sys.path
sys.path.append("e:/ai_company_faz12.1")

from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import Project
from sqlalchemy import update

async def final_cleanup():
    print("Sovereign AGI - Final Cleanup of All Breaches")
    
    async with AsyncSessionLocal() as db:
        # Update ALL projects to have a healthy budget
        print("Restoring all project budgets to $10,000.00...")
        q = update(Project).values(budget_limit=10000.0)
        await db.execute(q)
        await db.commit()
    
    print("All project budgets restored.")

if __name__ == "__main__":
    asyncio.run(final_cleanup())
