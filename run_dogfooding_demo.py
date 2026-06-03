import os
import sys
import asyncio

workspace_root = "/app" if os.path.exists("/app") else "e:/ai_company_faz12.1"
sys.path.append(workspace_root)

from services.self_repair_audit.audit_orchestrator import AuditOrchestrator
from services.workflow_api.ceo_router import approve_self_repair
from services.self_repair_audit.action_models import SuggestionActionRequest

from libs.db.session import session_scope, check_connectivity

async def run_demo():
    print("1. Running Audit to get fresh findings...")
    orch = AuditOrchestrator(workspace_root)
    report = orch.execute_full_audit()
    run_id = report.get("audit_run_id")
    print(f"Audit completed: {run_id}")
    
    # We will pick AUD-FIND-SEC-001 (direct_git_push)
    target_finding_id = None
    for f in report.get("findings", []):
        if "direct_git_push" in str(f) or f.get("category") == "security":
            target_finding_id = f.get("finding_id")
            break
            
    if not target_finding_id:
        print("No security findings found. Exiting.")
        return

    print(f"2. Simulating CEO Dashboard Approval for Finding: {target_finding_id}")
    
    req = SuggestionActionRequest(
        action="APPROVE_SELF_REPAIR",
        operator_id="ceo-demo-user",
        rationale="Dogfooding test execution",
        risk_acknowledgement=True
    )
    
    # Pre-check DB to initialize fallback if necessary
    check_connectivity()

    # We need a db session
    async with session_scope() as db:
        try:
            res = await approve_self_repair(
                suggestion_id=target_finding_id,
                body=req,
                audit_run_id=run_id,
                identity={"sub": "governor"},
                db=db
            )
            print("3. CEO Bridge response:")
            import pprint
            pprint.pprint(res)
            
            print("\n4. The taskflow is now queued. The Celery worker will pick it up and execute the SWE-Agent to fix this issue.")
        except Exception as e:
            print(f"Failed to trigger repair: {e}")

if __name__ == "__main__":
    asyncio.run(run_demo())
