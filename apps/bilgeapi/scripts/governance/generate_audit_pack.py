import asyncio
import sys
import argparse
from datetime import datetime, timezone, timedelta
from services.governance.auditor_service import AuditorService
from services.observability.logging import get_logger

logger = get_logger("scripts.audit_pack")

async def run_audit_pack(name: str, purpose: str, days: int):
    """Generates an audit package for the last N days."""
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    
    operator = "CLI_OPERATOR"
    
    print(f"Generating Audit Package: {name}")
    print(f"   Range: {start.isoformat()} to {end.isoformat()}")
    print(f"   Purpose: {purpose}")
    
    try:
        path = await AuditorService.create_and_export_bundle(name, purpose, start, end, operator)
        print(f"\nAudit Package Created Successfully!")
        print(f"Location: {path}")
    except Exception as e:
        print(f"\nError generating audit pack: {e}")
        logger.error(f"Audit pack failure: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Sovereign AGI Audit Package")
    parser.add_argument("--name", required=True, help="Name of the bundle")
    parser.add_argument("--purpose", required=True, help="Purpose (e.g. SOC2_Q2)")
    parser.add_argument("--days", type=int, default=30, help="Number of days to include")
    
    args = parser.parse_args()
    
    asyncio.run(run_audit_pack(args.name, args.purpose, args.days))
