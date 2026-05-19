import asyncio
import os
import uuid
from sqlalchemy import select
from libs.db.session import AsyncSessionLocal
from libs.db.models.auth_models import Operator, PermissionGrant

async def grant():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Operator).where(Operator.email == "bilgehan@faz.one"))
        op = res.scalar_one_or_none()
        if not op:
            print("Operator not found!")
            return
        
        # Check if already exists
        perms_res = await db.execute(select(PermissionGrant).where(
            PermissionGrant.operator_id == op.id,
            PermissionGrant.permission == "incident.view"
        ))
        if perms_res.scalar_one_or_none():
            print("Permission already granted.")
        else:
            db.add(PermissionGrant(
                operator_id=op.id,
                permission="incident.view",
                scope_type="global",
                effect="allow"
            ))
            print("Granted incident.view")

        perms_res2 = await db.execute(select(PermissionGrant).where(
            PermissionGrant.operator_id == op.id,
            PermissionGrant.permission == "approval.view"
        ))
        if perms_res2.scalar_one_or_none():
            print("Permission already granted.")
        else:
            db.add(PermissionGrant(
                operator_id=op.id,
                permission="approval.view",
                scope_type="global",
                effect="allow"
            ))
            print("Granted approval.view")
        
        await db.commit()
        print("Done.")

if __name__ == "__main__":
    os.environ["PYTHONPATH"] = "."
    asyncio.run(grant())
