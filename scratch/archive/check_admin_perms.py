import asyncio
from libs.db.session import AsyncSessionLocal
from libs.db.models.auth_models import Operator, PermissionGrant
from sqlalchemy import select

async def check_permissions():
    async with AsyncSessionLocal() as db:
        # 1. Admin'i bul
        res = await db.execute(select(Operator).where(Operator.email == "admin@sovereign.agi"))
        admin = res.scalar_one_or_none()
        
        if not admin:
            print("ERROR: Admin operator not found.")
            return

        print(f"--- Operator Info ---")
        print(f"ID: {admin.id}")
        print(f"Email: {admin.email}")
        print(f"Role: {admin.role}")
        print(f"Status: {'Active' if admin.is_active else 'Quarantined'}")
        
        # 2. İzinleri bul
        res = await db.execute(select(PermissionGrant).where(PermissionGrant.operator_id == admin.id))
        grants = res.scalars().all()
        
        print(f"\n--- Active Permission Grants ({len(grants)}) ---")
        if not grants:
            print("WARNING: No explicit permission grants found for this operator.")
            print("Action: System relies on Role-Based defaults if not defined.")
        else:
            for g in grants:
                print(f"- [{g.scope}] {g.permission}: {g.effect} (Reason: {g.justification or 'N/A'})")

if __name__ == "__main__":
    asyncio.run(check_permissions())
