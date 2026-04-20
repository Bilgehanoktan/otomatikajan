
import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from libs.db.session import AsyncSessionLocal
from sqlalchemy import text

async def remediate_enums():
    print("[*] Starting Database Enum Remediation...")
    
    mapping = {
        'MEDIUM':   ['orta', 'medium', 'NORMAL', 'MEDIUM'],
        'HIGH':     ['yüksek', 'high', 'YÜKSEK', 'YUKSEK', 'HIGH'],
        'LOW':      ['düşük', 'low', 'DÜŞÜK', 'DUSUK', 'LOW'],
        'CRITICAL': ['kritik', 'critical', 'KRİTİK', 'KRITIK', 'CRITICAL']
    }
    
    async with AsyncSessionLocal() as db:
        try:
            total_updated = 0
            for target_val, source_vals in mapping.items():
                placeholders = ", ".join([f"'{v}'" for v in source_vals])
                query = f"UPDATE projects SET priority = '{target_val}' WHERE priority IN ({placeholders});"
                res = await db.execute(text(query))
                rows = res.rowcount
                print(f"  [+] Updated {rows} records to '{target_val}'")
                total_updated += rows
            
            await db.commit()
            print(f"[*] Remediation Complete. Total records standardized: {total_updated}")
            
        except Exception as e:
            await db.rollback()
            print(f"[!] Remediation FAILED: {e}")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(remediate_enums())
