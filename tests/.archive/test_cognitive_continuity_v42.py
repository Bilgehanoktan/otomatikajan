import asyncio
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from packages.orchestration.agi.cognitive.sovereign_cortex import SovereignCortex
from packages.orchestration.agi.task_governance import GovernedTask, SovereignGoal, GovernanceStatus
from packages.orchestration.agi.operational.velocity_engine import EngineResult

class TestCognitiveContinuityV42(unittest.IsolatedAsyncioTestCase):
    
    async def test_monologue_persistence_and_injection(self):
        print("\n--- Phase 42: Cognitive Continuity Verification ---")
        
        # 1. Setup
        cortex = SovereignCortex()
        
        st = GovernedTask(
            id="task_1",
            agent_id="architect",
            prompt="Build a bridge",
            status=GovernanceStatus.PENDING,
            internal_monologue="Previously, I thought about using concrete."
        )
        
        parent = SovereignGoal(id="goal_1", title="Infrastructure", subtasks=[st])
        
        # 2. Mock ContextBuilder to verify injection
        with patch("packages.orchestration.agi.cognitive.sovereign_cortex.context_builder.build_context", new_callable=AsyncMock) as mock_ctx:
            mock_ctx.return_value = "Enriched Context Content"
            
            # 3. Mock VelocityEngine to verify capture
            mock_result = EngineResult(
                success=True,
                output_data="Bridge built.",
                reflection="Decided to use steel instead of concrete."
            )
            
            with patch("packages.orchestration.agi.operational.velocity_engine.velocity_engine.simulate_and_execute", new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = mock_result
                
                # Execute node logic
                await cortex._execute_subtask_nexus(st, parent)
                
                # Verify Injection
                args, kwargs = mock_ctx.call_args
                self.assertEqual(kwargs.get("internal_monologue"), "Previously, I thought about using concrete.")
                print("Monologue Injection: SUCCESS (Previous thread restored)")
                
                # Verify Capture
                self.assertEqual(st.internal_monologue, "Decided to use steel instead of concrete.")
                print("Monologue Capture: SUCCESS (New reasoning persisted)")

if __name__ == "__main__":
    unittest.main()
