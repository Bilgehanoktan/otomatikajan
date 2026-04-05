
import asyncio
import os
import sys
import logging
from datetime import datetime, timedelta, timezone

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.models import Memory
from db.session import AsyncSessionLocal
from core.agi.cognitive.sovereign_cortex import sovereign_cortex
from core.agi.consciousness.affective_core import affective_core

logging.basicConfig(level=logging.INFO)
_log = logging.getLogger("VERIFY-V59")

async def verify_dream_cycle():
    _log.info("--- Phase 59 Cognitive Compaction Test Started ---")
    
    # 1. Havuzu temizle ve test verisi ekle
    async with AsyncSessionLocal() as db:
        # Eski gürültü ekle (Daha önceden tanımlanmış bir zaman damgasıyla)
        old_time = datetime.now(timezone.utc) - timedelta(hours=72)
        
        # 5 adet gürültü (Prune edilecek)
        for i in range(5):
            m = Memory(
                agent_id="test_noise_agent",
                body=f"Ephemeral log {i}: Connection attempt {i}",
                category="debug_logs",
                importance=0.1,
                created_at=old_time
            )
            db.add(m)
        
        # 3 adet benzer anı (Consolidate edilecek)
        for i in range(3):
            m = Memory(
                agent_id="test_redundant_agent",
                body=f"Failed to connect to Service X because of Timeout {i}",
                category="connection_errors",
                importance=0.5
            )
            db.add(m)
            
        await db.commit()
    
    # 2. Enerjiyi düşür (ECO Modu tetikle)
    affective_core.state["energy_reserve"] = 0.1
    _log.info(f"System Energy set to {affective_core.energy} (Low Energy Trigger)")

    # 3. SovereignCortex.coordinate_goal çağırmaya çalış (Planlamaya geçmeden rüya görecek)
    _log.info("Scenario: Triggering Project that should auto-dream due to low energy")
    try:
        # Hafif bir görev başlat
        await sovereign_cortex.coordinate_goal(
            title="Maintainence Task",
            description="Testing cognitive compaction via low energy trigger."
        )
    except Exception as e:
        _log.warning(f"Note: Execute might fail later due to 429s, but dream cycle should have run first: {e}")

    # 4. Veritabanı durumunu kontrol et
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select, func
        
        # debug_logs kalmış mı? (0 olmalı)
        stmt_noise = select(func.count(Memory.id)).where(Memory.category == "debug_logs")
        noise_count = (await db.execute(stmt_noise)).scalar()
        
        # connection_errors ne durumda? (0 olmalı, 1 adet semantic_wisdom oluşmuş olmalı)
        stmt_redundant = select(func.count(Memory.id)).where(Memory.category == "connection_errors")
        redundant_count = (await db.execute(stmt_redundant)).scalar()
        
        stmt_wisdom = select(func.count(Memory.id)).where(Memory.category == "semantic_wisdom")
        wisdom_count = (await db.execute(stmt_wisdom)).scalar()

        _log.info(f"Results:")
        _log.info(f"  > Noise Count (debug_logs): {noise_count} (Expected 0)")
        _log.info(f"  > Redundant Count (connection_errors): {redundant_count} (Expected 0)")
        
        if noise_count == 0 and redundant_count == 0:
            _log.info("v SUCCESS: Dreaming Cycle pruned and consolidated successfully!")
        else:
            _log.error("x FAILED: Memories were not pruned/consolidated correctly.")

    _log.info("--- Phase 59 Verification COMPLETED ---")

if __name__ == "__main__":
    asyncio.run(verify_dream_cycle())
