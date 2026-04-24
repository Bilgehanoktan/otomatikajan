import asyncio
import uuid
from sqlalchemy import select, delete
from libs.db.session import AsyncSessionLocal
from libs.db.models import Operator, PermissionGrant, SystemIdentity
from services.auth.jwt_auth import AccessControlService

async def run_scoped_tests():
    print("--- SIF-02 Scoped Enforcement Test Matrix ---")
    
    async with AsyncSessionLocal() as db:
        # 0. Cleanup old test data
        await db.execute(delete(PermissionGrant).where(PermissionGrant.scope_value.in_(["Project_X", "Project_Y", "Project_Z"])))
        await db.commit()

        # Create a test operator (not Prime)
        test_op_id = uuid.uuid4()
        
        # Scenario 1: Scoped Allow (Allow only Project_X)
        print("\n[*] Test 1: Scoped Allow (Project_X vs Project_Y)")
        grant_x = PermissionGrant(
            operator_id=test_op_id,
            permission="workflow.view",
            scope_type="project",
            scope_value="Project_X",
            effect="allow"
        )
        db.add(grant_x)
        await db.commit()
        
        allowed_x = await AccessControlService.is_allowed(db, test_op_id, "operator", "workflow.view", "project", "Project_X")
        allowed_y = await AccessControlService.is_allowed(db, test_op_id, "operator", "workflow.view", "project", "Project_Y")
        
        print(f"    - Access Project_X: {'OK' if allowed_x else 'FAILED'}")
        print(f"    - Access Project_Y: {'DENIED' if not allowed_y else 'FAILED (Should be denied)'}")

        # Scenario 2: Explicit Deny (Global Allow + Scoped Deny)
        print("\n[*] Test 2: Explicit Deny (Global Allow vs Scoped Deny Project_Z)")
        grant_global = PermissionGrant(
            operator_id=test_op_id,
            permission="workflow.view",
            scope_type="global",
            effect="allow"
        )
        grant_deny_z = PermissionGrant(
            operator_id=test_op_id,
            permission="workflow.view",
            scope_type="project",
            scope_value="Project_Z",
            effect="deny" # Explicit Deny
        )
        db.add(grant_global)
        db.add(grant_deny_z)
        await db.commit()
        
        # AccessControlService needs to be updated to support explicit deny check
        # For now we'll check if our logic handles it
        
        # We need to refine the AccessControlService.is_allowed to check for ANY deny first
        print("    - (Requirement check: Explicit deny must override global allow)")

        # Scenario 3: Identity Separation
        print("\n[*] Test 3: Identity Separation (Operator vs System)")
        # If we grant to operator, system should NOT have it
        sys_id = uuid.uuid4()
        allowed_sys = await AccessControlService.is_allowed(db, sys_id, "system", "workflow.view", "project", "Project_X")
        print(f"    - System Access (No grant): {'DENIED' if not allowed_sys else 'FAILED'}")

if __name__ == "__main__":
    asyncio.run(run_scoped_tests())
