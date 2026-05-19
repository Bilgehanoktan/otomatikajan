
import asyncio
import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

async def test_audit():
    from libs.config import DATABASE_URL
    print(f"Starting proactive audit on: {DATABASE_URL}")
    from libs.diagnostics.auditor import InfrastructureAuditor
    # We run the report which saves to DB
    await InfrastructureAuditor.run_and_report()
    
    # We also fetch findings separately for display in this test
    findings = InfrastructureAuditor.audit_db_schema()
    
    if not findings:
        print("PASS: No drifts detected.")
    else:
        print(f"WARN: Found {len(findings)} drifts reported to database.")
        for f in findings:
            print(f"- [{f['subtype']}] {f['message']}")
            print(f"  Fix: {f['suggested_fix']['command']}")
            print("-" * 20)

if __name__ == "__main__":
    asyncio.run(test_audit())
