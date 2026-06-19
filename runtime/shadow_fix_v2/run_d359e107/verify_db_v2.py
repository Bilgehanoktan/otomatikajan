
import asyncio
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from libs.db.session import AsyncSessionLocal, is_db_degraded, db_error
from libs.db.models.core_models import OperationalIncident, SovereignEvidence
from libs.db.models.auth_models import Operator
from sqlalchemy import select, func

async def verify():
    print(f"--- DB STATUS ---")
    print(f"Is Degraded (SQLite Fallback): {is_db_degraded()}")
    print(f"DB Error: {db_error()}")
    
    async with AsyncSessionLocal() as db:
        # Check Operators
        try:
            op_count = await db.scalar(select(func.count(Operator.id)))
            print(f"Operators: {op_count}")
        except Exception as e:
            print(f"Error checking Operators: {e}")
            
        # Check Incidents
        try:
            incident_count = await db.scalar(select(func.count(OperationalIncident.id)))
            print(f"Incidents: {incident_count}")
        except Exception as e:
            print(f"Error checking Incidents: {e}")
        
        # Check Axiology Evidence
        try:
            evidence_count = await db.scalar(select(func.count(SovereignEvidence.id)).where(SovereignEvidence.evidence_type == "axiology_audit"))
            print(f"Axiology Evidence (Audit): {evidence_count}")
            
            total_evidence = await db.scalar(select(func.count(SovereignEvidence.id)))
            print(f"Total Evidence: {total_evidence}")
        except Exception as e:
            print(f"Error checking Evidence: {e}")

if __name__ == "__main__":
    asyncio.run(verify())
