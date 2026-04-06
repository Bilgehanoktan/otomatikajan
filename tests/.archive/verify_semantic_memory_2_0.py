import asyncio
import logging
import uuid
from datetime import datetime, timezone

from packages.orchestration.agi.cognitive.synaptic_cortex import synaptic_cortex
from packages.orchestration.agi.learning.memory_distiller import memory_distiller
from packages.persistence.session import AsyncSessionLocal
from packages.persistence.repository import MemoryRepository

logging.basicConfig(level=logging.INFO)
_log = logging.getLogger("verify_memory_2_0")

async def test_synergetic_retrieval():
    """Phase 71: Synergetic Retrieval Test"""
    _log.info("Testing Synergetic Retrieval...")
    async with AsyncSessionLocal() as db:
        # Save a sample lesson
        await synaptic_cortex.save(
            db, 
            agent_id="test_agent", 
            body="Use specialized regex for path extraction to avoid false positives.", 
            category="lesson",
            tags=["regex", "paths"]
        )
        await packages.persistence.commit()
        
        # Test search
        results = await synaptic_cortex.search_synergetic(db, "regex", top_k=3)
        _log.info(f"Retrieved {len(results)} synergetic results.")
        for r in results:
            _log.info(f" - [{r.get('category')}] {r.get('body')[:50]}...")
        
        assert len(results) > 0, "Should find at least 1 result"

async def test_rule_distillation():
    """Phase 73: Rule Distillation Test"""
    _log.info("Testing Rule Distillation...")
    async with AsyncSessionLocal() as db:
        # 1. Create mock recurring failures
        # Note: Patterns must match early (first 60 chars) to trigger distillation grouping
        for i in range(3):
            await MemoryRepository.create(
                db,
                agent_id="coder",
                body=f"CRITICAL ERROR: Directory not found during execution in step {i}. Path normalization is missing in the core/utils/file_handler.py module.",
                category="negative_lesson",
                importance=0.6,
                tags=["path_error"]
            )
        await packages.persistence.commit()

    # 2. Run distillation cycle
    _log.info("Running distillation cycle...")
    await memory_distiller.run_distillation_cycle()
    
    # 3. Verify rule creation (Check logs or DB)
    async with AsyncSessionLocal() as db:
        rules = await synaptic_cortex.search(db, "SİSTEM KURALI", category="system_instinct")
        _log.info(f"Distilled Rules found: {len(rules)}")
        for r in rules:
            _log.info(f" - RULE: {r['body']}")
        
        assert len(rules) > 0, "Memory distiller should have created at least one rule"

async def main():
    try:
        await test_synergetic_retrieval()
        await test_rule_distillation()
        _log.info("SEMANTIC MEMORY 2.0 VERIFICATION COMPLETE!")
    except Exception as e:
        _log.error(f"Verification FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(main())
