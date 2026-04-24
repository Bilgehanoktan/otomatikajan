import asyncio
import uuid
from libs.db.session import AsyncSessionLocal
from libs.db.models.auth_models import Operator, PermissionGrant
from sqlalchemy import select

async def grant_admin_powers():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Operator).where(Operator.email == "admin@sovereign.agi"))
        admin = res.scalar_one_or_none()
        
        if not admin:
            print("ERROR: Admin operator not found.")
            return

        permissions = [
            ("workflow.manage", "global", "ALLOW", "SIF-03 Root Administrative Access"),
            ("governance.override", "global", "ALLOW", "Emergency Governance Control"),
            ("system.repair", "global", "ALLOW", "Autonomous Repair Supervision"),
            ("identity.manage", "global", "ALLOW", "Identity Fabric Management")
        ]
        
        for perm, scope, effect, reason in permissions:
            # Mevcut mu kontrol et
            check = await db.execute(select(PermissionGrant).where(
                PermissionGrant.operator_id == admin.id,
                PermissionGrant.permission == perm,
                PermissionGrant.scope == scope
            ))
            if not check.scalar_one_or_none():
                grant = PermissionGrant(
                    id=uuid.uuid4(),
                    operator_id=admin.id,
                    permission=perm,
                    scope=scope,
                    effect=effect,
                    justification=reason,
                    granted_by="SYSTEM_INITIALIZER"
                )
                db.add(grant)
                print(f"GRANTED: {perm} [{scope}] -> {effect}")
        
        await db.commit()
        print("\nSUCCESS: Admin permission matrix fully populated.")

if __name__ == "__main__":
    asyncio.run(grant_admin_powers())
