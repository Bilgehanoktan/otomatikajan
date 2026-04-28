
import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from libs.db.session import AsyncSessionLocal
from sqlalchemy import bindparam, text

async def remediate_enums():
    print("[*] Starting Database Enum Remediation...")
    
    mapping = {
        'MEDIUM':   ['orta', 'medium', 'NORMAL', 'MEDIUM'],
        'HIGH':     ['yüksek', 'high', 'YÜKSEK', 'YUKSEK', 'HIGH'],
        'LOW':      ['düşük', 'low', 'DÜŞÜK', 'DUSUK', 'LOW'],
        'CRITICAL': ['kritik', 'critical', 'KRİTİK', 'KRITIK', 'CRITICAL']
    }
    
    update_stmt = text(
        "UPDATE projects SET priority = :target WHERE priority IN :source_values"
    ).bindparams(bindparam("source_values", expanding=True))

    async with AsyncSessionLocal() as db:
        try:
            total_updated = 0
            for target_val, source_vals in mapping.items():
                res = await db.execute(
                    update_stmt,
                    {"target": target_val, "source_values": tuple(source_vals)},
                )
                rows = res.rowcount or 0
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
