import asyncio
import uuid
from sqlalchemy import select, update
from libs.db.session import AsyncSessionLocal
from libs.db.models.auth_models import Operator

async def upgrade_operators():
    async with AsyncSessionLocal() as db:
        print("Checking for AUDIT_OBSERVER operators...")
        res = await db.execute(select(Operator).where(Operator.role == "AUDIT_OBSERVER"))
        observers = res.scalars().all()
        
        if not observers:
            print("No AUDIT_OBSERVER found.")
            # Check all operators just in case
            res = await db.execute(select(Operator))
            all_ops = res.scalars().all()
            for op in all_ops:
                print(f"Operator: {op.email}, Role: {op.role}")
            return

        for obs in observers:
            print(f"Upgrading {obs.email} from AUDIT_OBSERVER to OPERATOR...")
            obs.role = "OPERATOR"
        
        await db.commit()
        print("Upgrade complete.")

if __name__ == "__main__":
    asyncio.run(upgrade_operators())
