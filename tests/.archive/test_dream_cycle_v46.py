import asyncio
import pytest
from unittest.mock import AsyncMock, patch
from packages.orchestration.application.job_queue import JobQueue, JobStatus
from packages.orchestration.agi.cognitive.subconscious_cortex_45 import subconscious_cortex_45
from packages.orchestration.agi.cognitive.decomposer import GoalDecomposer
from packages.persistence.models import Memory

@pytest.mark.asyncio
async def test_dream_cycle_and_wisdom_injection():
    """
    Phase 46 Validation:
    Dream -> Audit -> Wisdom -> Planning
    """
    # 1. Setup
    queue = JobQueue(concurrency=1)
    decomposer = GoalDecomposer()
    
    # Register the dream handler (as done in lifespan)
    async def _run_dream_wrapper(**payload):
        from packages.persistence.session import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            return await subconscious_cortex_45.dream(db)
    
    queue.register("system_dream", _run_dream_wrapper)
    
    # 2. Mock model_orch to simulate Dream Synthesis & Adversarial Audit
    with patch("packages.orchestration.agi.cognitive.subconscious_cortex_45.subconscious_cortex_45.model_orch.complete_task", new_callable=AsyncMock) as mock_complete:
        
        # First call: Dream Synthesis
        # Second call: Adversarial Audit (is_valid: true)
        mock_complete.side_effect = [
            # Dream Synthesis Response
            AsyncMock(content='{"universal_lessons": ["Test Lesson 1"], "suggested_policies": [{"title": "Test Policy", "rule": "Always test", "reason": "Reliability"}]}'),
            # Policy Audit Response
            AsyncMock(content='{"is_valid": true, "critique": "Approved"}'),
            # Decomposer planning response
            AsyncMock(content='{"reasoning": "Based on wisdom", "plan": []}')
        ]
        
        # 3. Trigger Dream
        job = await queue.enqueue("system_dream")
        worker_task = asyncio.create_task(queue.start(num_workers=1))
        
        timeout = 10.0
        start = asyncio.get_event_loop().time()
        while job.status != JobStatus.COMPLETED and (asyncio.get_event_loop().time() - start) < timeout:
            await asyncio.sleep(0.5)
        
        await queue.stop()
        assert job.status == JobStatus.COMPLETED
        print("✅ Dream Cycle (Synthesis + Audit) PASSED!")

        # 4. Verify Wisdom Injection in Planning
        # We need memories/wisdoms to be returned by synaptic_cortex.search
        with patch("packages.orchestration.agi.cognitive.goal_decomposer.synaptic_cortex.search", new_callable=AsyncMock) as mock_search:
            mock_search.side_effect = [
                [], # Memories
                [{"body": " INTERNALIZED WISDOM: Always test everything."}] # Wisdoms
            ]
            
            # Now trigger decompose
            plan = await decomposer.decompose("Test Task", "Test Desc", [])
            
            # Verify that complete_task was called with wisdom
            # The last call to mock_complete was for planning
            planning_call_args = mock_complete.call_args[1]
            prompt = planning_call_args.get("prompt", "")
            
            assert "ÖĞRENİLMİŞ BİLGELİK" in prompt
            assert "Always test everything" in prompt
            print("✅ Wisdom Injection in Planning PASSED!")

if __name__ == "__main__":
    asyncio.run(test_dream_cycle_and_wisdom_injection())
