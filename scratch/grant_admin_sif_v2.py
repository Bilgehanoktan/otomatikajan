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
            ("workflow.manage", "global", None, "ALLOW"),
            ("governance.override", "global", None, "ALLOW"),
            ("system.repair", "global", None, "ALLOW"),
            ("identity.manage", "global", None, "ALLOW")
        ]
        
        for perm, s_type, s_val, effect in permissions:
            # Mevcut mu kontrol et
            check = await db.execute(select(PermissionGrant).where(
                PermissionGrant.operator_id == admin.id,
                PermissionGrant.permission == perm,
                PermissionGrant.scope_type == s_type,
                PermissionGrant.scope_value == s_val
            ))
            if not check.scalar_one_or_none():
                grant = PermissionGrant(
                    id=uuid.uuid4(),
                    operator_id=admin.id,
                    permission=perm,
                    scope_type=s_type,
                    scope_value=s_val,
                    effect=effect,
                    granted_by=admin.id # Self-provisioned for initial setup
                )
                db.add(grant)
                print(f"GRANTED: {perm} [{s_type}:{s_val}] -> {effect}")
        
        await db.commit()
        print("\nSUCCESS: Admin permission matrix fully populated (SIF-01/03 Compliant).")

if __name__ == "__main__":
    asyncio.run(grant_admin_powers())
