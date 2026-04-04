import asyncio
import uuid
import logging
from datetime import datetime, timezone
from sqlalchemy import select
from db.session import AsyncSessionLocal, init_db
from db.models import ImprovementOpportunity
from core.agi.cognitive.metacognitive_auditor import metacognitive_auditor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_resilience")

async def test_auditor_upsert():
    logger.info("Testing MetacognitiveAuditor UPSERT resilience...")
    await init_db()
    
    agent_id = f"test_agent_{uuid.uuid4().hex[:6]}"
    skill_id = "test_skill"
    bn = {"agent_id": agent_id, "skill_id": skill_id}
    data = {
        "root_cause": "Initial Root Cause",
        "repair_action": "Initial Action",
        "repair_detail": "Initial Detail",
        "urgency": "high"
    }
    
    async with AsyncSessionLocal() as db:
        # 1. First record
        logger.info("Inserting first record...")
        await metacognitive_auditor._create_improvement_opportunity(db, data, bn)
        await db.commit()
        
        # 2. Duplicate record (different data, same hash)
        logger.info("Attempting duplicate record (UPSERT branch)...")
        data["root_cause"] = "Updated Root Cause"
        await metacognitive_auditor._create_improvement_opportunity(db, data, bn)
        await db.commit()
        
        # 3. Verify
        p_hash = ImprovementOpportunity.generate_hash("cog_diag", f"{agent_id}:{skill_id}")
        result = await db.execute(select(ImprovementOpportunity).where(ImprovementOpportunity.pattern_hash == p_hash))
        opps = result.scalars().all()
        
        logger.info(f"Opportunities found for hash: {len(opps)}")
        for o in opps:
            logger.info(f" - ID: {o.id}, Desc: {o.description[:50]}...")
            
        assert len(opps) == 1, "Should only have one record (UPSERT failed)"
        assert "Updated Root Cause" in opps[0].description, "Record was not updated"
        logger.info("✓ Test Passed: UPSERT logic is working.")

if __name__ == "__main__":
    asyncio.run(test_auditor_upsert())
