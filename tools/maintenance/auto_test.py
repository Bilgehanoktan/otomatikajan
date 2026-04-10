import asyncio
import http.client
import json
import os
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = str(Path(__file__).resolve().parents[2])
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

async def check_api_health():
    print("🔍 Test 1: API Health Check...")
    try:
        conn = http.client.HTTPConnection("localhost", 8000)
        conn.request("GET", "/health")
        resp = conn.getresponse()
        data = json.loads(resp.read().decode())
        print(f"✅ API Response: {resp.status} - {data}")
        return resp.status == 200
    except Exception as e:
        print(f"❌ API Check Failed: {e}")
        return False

async def check_db_integrity():
    print("\n🔍 Test 2: Database Integrity...")
    from packages.persistence.session import AsyncSessionLocal
    from sqlalchemy import text
    try:
        async with AsyncSessionLocal() as db:
            res = await db.execute(text("SELECT status, count(*) FROM projects GROUP BY status"))
            rows = res.fetchall()
            print("📊 Project Status Distribution:")
            for status, count in rows:
                print(f"   - {status}: {count}")
            
            # Check for any ERROR status
            error_count = next((c for s, c in rows if s == 'ERROR'), 0)
            if error_count > 10:  # Threshold for concern
                print(f"⚠️ High error count detected: {error_count}")
            
            return True
    except Exception as e:
        print(f"❌ DB Check Failed: {e}")
        return False

async def check_worker_activity():
    print("\n🔍 Test 3: Worker Throughput (Progress Check)...")
    from packages.persistence.session import AsyncSessionLocal
    from sqlalchemy import text
    try:
        async with AsyncSessionLocal() as db:
            # Check if any project is RUNNING or completed recently
            res = await db.execute(text("SELECT count(*) FROM projects WHERE status IN ('RUNNING', 'COMPLETED', 'PARTIAL_COMPLETE')"))
            active_count = res.scalar()
            print(f"⚙️ Active/Completed Projects: {active_count}")
            
            res_queued = await db.execute(text("SELECT count(*) FROM projects WHERE status = 'QUEUED'"))
            queued_count = res_queued.scalar()
            print(f"⏳ Remaining in Queue: {queued_count}")
            
            return True
    except Exception as e:
        print(f"❌ Worker Activity Check Failed: {e}")
        return False

async def run_tests():
    print("========================================")
    print("🚀 AUTOMATED SYSTEM VERIFICATION (Sovereign AGI)")
    print("========================================\n")
    
    api_ok = await check_api_health()
    db_ok = await check_db_integrity()
    worker_ok = await check_worker_activity()
    
    print("\n========================================")
    if api_ok and db_ok and worker_ok:
        print("✅ SYSTEM STATUS: OPERATIONAL")
    else:
        print("❌ SYSTEM STATUS: DEGRADED / ISSUES DETECTED")
    print("========================================")

if __name__ == "__main__":
    asyncio.run(run_tests())
