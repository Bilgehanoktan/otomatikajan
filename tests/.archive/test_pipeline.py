import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from packages.orchestration.agi.orchestrator import AGIOrchestrator
from packages.orchestration.agi.schemas import SourceType, TaskType, RiskLevel

class TestAGIPipeline(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Mock LLM
        self.mock_model = MagicMock()
        self.mock_model.generate = AsyncMock()
        
        # Mock DB
        self.mock_db = AsyncMock()
        self.patcher_session = unittest.mock.patch("packages.persistence.session.session_scope", return_value=MagicMock(__aenter__=AsyncMock(return_value=self.mock_db), __aexit__=AsyncMock()))
        self.patcher_session.start()

        self.patcher_store = unittest.mock.patch("packages.memory.store.memory_store.memory_write_gate", AsyncMock(return_value=True))
        self.patcher_store.start()
        
        self.patcher_save = unittest.mock.patch("packages.memory.store.memory_store.save_episode", AsyncMock())
        self.patcher_save.start()

        # Interpreter Mock Response
        self.mock_model.generate.side_effect = [
            # 1. Interpreter Response
            '{"task_type": "analysis", "objective": "Test task", "risk_level": "low"}',
            # 2. Planner Response
            '{"steps": [{"step_id": "step1", "agent_id": "architect", "action": "test", "params": {}, "dependencies": []}], "tool_requirements": ["test"], "estimated_risk": "low"}',
            # 3. Audit Response
            '{"result_status": true, "evidence_summary": "Passed", "confidence_adjusted": 0.9, "integration_reality_score": 0.8, "safe_to_finalize": true}'
        ]
        
        self.orch = AGIOrchestrator(model_orch=self.mock_model)
        # Mock agents
        self.orch.agents = {
            "architect": MagicMock(execute=AsyncMock(return_value=MagicMock(raw_output="Mock Output")))
        }
        self.orch.executor.agents = self.orch.agents

    async def asyncTearDown(self):
        self.patcher_session.stop()
        self.patcher_store.stop()
        self.patcher_save.stop()

    async def test_full_flow(self):
        # Run orchestrator
        episode = await self.orch.run("Kodu analiz et", source=SourceType.USER_MESSAGE)
        
        # Assertions
        self.assertIsNotNone(episode.episode_id)
        self.assertEqual(episode.problem_frame.task_type, TaskType.ANALYSIS)
        self.assertEqual(len(episode.plan.steps), 1)
        self.assertTrue(episode.verification.result_status)
        self.assertEqual(episode.final_output, "Mock Output")
        print(f"Test Successful: Episode {episode.episode_id}")

if __name__ == "__main__":
    unittest.main()
