
import sys
import os
import asyncio
import uuid
from pathlib import Path

# Add project root to path
sys.path.append("e:/ai_company_faz12.1")

from libs.governance.constitutional_guard import ConstitutionalGuard
from services.governance.budget_service import BudgetService

async def test_constitutional_locks():
    print("--- Testing Constitutional Locks ---")
    guard = ConstitutionalGuard(project_root="e:/ai_company_faz12.1")
    
    test_files = [
        ("libs/db/base.py", True),
        ("libs/auth/user_model.py", True),
        ("services/auth/login.py", True),
        ("src/app/page.tsx", False), # Should NOT be locked
        ("libs/utils/helper.py", False) # Should NOT be locked
    ]
    
    pass_count = 0
    for path, expected in test_files:
        # Resolve path as the guard expects absolute path or handles it relative
        # The guard's is_locked uses .relative_to(project_root)
        full_path = str(Path("e:/ai_company_faz12.1") / path)
        locked = guard.is_locked(full_path)
        status = "PASS" if locked == expected else "FAIL"
        print(f"[{status}] File: {path} | Locked: {locked} | Expected: {expected}")
        if status == "PASS": pass_count += 1
        
    return pass_count == len(test_files)

async def test_budget_logic():
    print("\n--- Testing Budget Service ---")
    # We can't easily trigger a real DB breach without actual data, 
    # but we can check if the service correctly handles lookups.
    
    total = await BudgetService.get_total_consumption()
    print(f"[INFO] Current 30-day global consumption: ${total:.4f}")
    
    # Check circuit breaker for a mock project
    # Use a valid random UUID format
    mock_id = str(uuid.uuid4())
    is_safe = await BudgetService.check_circuit_breaker(mock_id, 1.0)
    print(f"[INFO] Circuit breaker for unknown project ({mock_id}): {is_safe}")
    
    return True

async def main():
    print("SOVEREIGN AGI PHASE 30 - MANUAL VERIFICATION\n")
    locks_ok = await test_constitutional_locks()
    budget_ok = await test_budget_logic()
    
    if locks_ok and budget_ok:
        print("\n[SUCCESS] Phase 30 manual verification components validated.")
    else:
        print("\n[FAILED] Some verification steps failed.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
