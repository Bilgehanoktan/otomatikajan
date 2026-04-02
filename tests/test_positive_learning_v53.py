import asyncio
import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List
from dataclasses import dataclass

# Mock objects to simulate the AGI environment
@dataclass
class MockSubTask:
    id: str
    prompt: str
    agent_id: str
    is_complex: bool = False

@dataclass
class MockTask:
    title: str
    subtasks: List[MockSubTask]
    status: str = "COMPLETED"

async def test_positive_learning():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("test_v53")
    
    logger.info("Testing Autonomous Skill Synthesis (Phase 53)...")
    
    # 1. MetacognitiveAuditor import (Actual implementation)
    from core.agi.cognitive.metacognitive_auditor import metacognitive_auditor
    from core.agi.cognitive.synaptic_cortex import synaptic_cortex
    from db.session import session_scope
    
    # 2. Mock a successful complex task
    mock_subtasks = [
        MockSubTask(id="st1", prompt="Initial scafolding", agent_id="architect", is_complex=True),
        MockSubTask(id="st2", prompt="DB schema design", agent_id="database_admin", is_complex=False),
        MockSubTask(id="st3", prompt="Recursive logic impl", agent_id="senior_developer", is_complex=True)
    ]
    
    mock_goal_title = "Build a Sovereign Recursive Engine"
    
    logger.info(f"Triggering positive distillation for: {mock_goal_title}")
    
    async with session_scope() as db:
        # Clear previous wisdom for clean test (optional, but let's just search after)
        
        # 3. Call the new method
        await metacognitive_auditor.distill_positive_skill(db, mock_goal_title, mock_subtasks)
        
        # 4. Verify in SynapticCortex
        logger.info("Verifying storage in SynapticCortex...")
        memories = await synaptic_cortex.search(
            db=db,
            query=mock_goal_title,
            category="semantic_wisdom",
            top_k=5
        )
        
        if len(memories) > 0:
            wisdom = memories[0]
            logger.info("SUCCESS: Positive Strategic Wisdom found!")
            logger.info(f"Distilled Body: {wisdom['body'][:200]}...")
            logger.info(f"Metadata: {json.dumps(wisdom.get('metadata', {}), indent=2)}")
            
            # Check for key fields in body (Strategic Wisdom format)
            if "STRATEGIC WISDOM:" in wisdom['body'] and "KEY INSIGHT:" in wisdom['body']:
                print("\n[PHASE 53 VERIFIED] Autonomous Skill Synthesis is ACTIVE and WORKING.\n")
            else:
                logger.error("Wisdom body format mismatch.")
                exit(1)
        else:
            logger.error("FAILURE: No Strategic Wisdom found in memory.")
            exit(1)

if __name__ == "__main__":
    asyncio.run(test_positive_learning())
