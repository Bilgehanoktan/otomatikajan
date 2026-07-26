import asyncio
import sys
import json
import argparse
from datetime import datetime, timezone, timedelta
from libs.governance.launch_gatekeeper import LaunchGatekeeper
from services.governance.auditor_service import AuditorService
from libs.db.session import get_db, get_db_ctx
from libs.db.models.core_models import Project, ProjectStatus
from services.observability.logging import get_logger
from sqlalchemy import update

logger = get_logger("scripts.handover")

async def run_production_handover(project_id: str, dry_run: bool):
    """
    Formal Production Handover Ritual.
    1. Run Pre-flight Checks (LaunchGatekeeper)
    2. If passed, generate a 'LAUNCH_READY' Audit Bundle
    3. If not dry_run, update project state to 'COMPLETED' or a custom 'LIVE' if exists.
    """
    print("Sovereign AGI -- Production Handover Protocol Initiated")
    print(f"Project ID: {project_id}")
    print(f"Dry Run: {dry_run}")
    print("==========================================================")
    
    # 1. Gatekeeper Verification
    print("\nStep 1: Executing Pre-flight Gatekeeper Checks...")
    passed, results = await LaunchGatekeeper.validate_for_rollout()
    
    for category, detail in results.items():
        status_icon = "[PASS]" if detail["status"] == "PASS" else "[FAIL]"
        print(f"   {status_icon} {category.capitalize()}: {json.dumps(detail)}")
    
    if not passed:
        print("\nHANDOVER ABORTED: System does not meet production criteria.")
        sys.exit(1)
    
    print("\nStep 1: Pre-flight Checks Passed.")

    # 2. Evidence Bundling
    print("\nStep 2: Generating Final Launch Evidence Bundle...")
    try:
        path = await AuditorService.create_and_export_bundle(
            name=f"LAUNCH_{project_id[:8]}",
            purpose="FINAL_PRODUCTION_HANDOVER",
            start=datetime.now(timezone.utc) - timedelta(days=7),
            end=datetime.now(timezone.utc),
            operator="CLI_OPERATOR"
        )
        print(f"   Bundle generated: {path}")
    except Exception as e:
        print(f"   Failed to generate launch bundle: {e}")
        if not dry_run: sys.exit(1)

    # 3. Final Handover Event
    if dry_run:
        print("\nStep 3: [DRY-RUN] Would seal production status now.")
        print("\nDRY-RUN COMPLETE. System would be LIVE.")
    else:
        print("\nStep 3: Sealing Production Status...")
        try:
            async with get_db_ctx() as db:
                # Update project to show it is now production-hardened
                await db.execute(
                    update(Project)
                    .where(Project.id == project_id)
                    .values(
                        status=ProjectStatus.COMPLETED, # Or custom state
                        notes=f"Production handover completed at {datetime.now(timezone.utc).isoformat()}"
                    )
                )
                await db.commit()
            print("\nPRODUCTION HANDOVER COMPLETE. System is now officially LIVE.")
        except Exception as e:
            print(f"\nError updating project status: {e}")
            sys.exit(1)
            
    print("==========================================================")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Perform Production Handover")
    parser.add_argument("--project", required=True, help="Project ID to handover")
    parser.add_argument("--dry-run", action="store_true", help="Run checks without modifying state")
    
    args = parser.parse_args()
    
    asyncio.run(run_production_handover(args.project, args.dry_run))
