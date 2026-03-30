import asyncio
import unittest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from core.agi.central_executive import CentralExecutive
from core.agi.schemas import SourceType, TaskType, RiskLevel

class TestCognitiveArchitecture(unittest.IsolatedAsyncioTestCase):
    """
    Bilişsel Mimari Entegrasyon Testleri (Faz 15.4 Total Lockdown).
    Central Executive, Perception Unit, Decision Matrix ve Motor Subsystem bütünselliğini doğrular.
    Hiçbir gerçek HTTP çağrısına (403 önleyici) izin vermez.
    """
    async def asyncSetUp(self):
        # 1. TOTAL HTTP LOCKDOWN (Patching httpx globally)
        self.patcher_http = patch("httpx.AsyncClient.post", AsyncMock())
        self.mock_http_post = self.patcher_http.start()
        
        # Default Success Response for any direct HTTP calls
        self.mock_http_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"choices": [{"message": {"content": "{}"}}], "content": [{"text": "{}"}]}
        )

        # 2. Logic Mocks (ModelOrchestrator levels)
        self.patcher_orch_task = patch("llm.model_orchestrator.ModelOrchestrator.complete_task", AsyncMock())
        self.patcher_orch_gen = patch("llm.model_orchestrator.ModelOrchestrator.generate", AsyncMock())
        self.mock_complete = self.patcher_orch_task.start()
        self.mock_generate = self.patcher_orch_gen.start()

        # Mock Responses
        self.mock_generate.return_value = '{"task_type": "analysis", "objective": "Otonom Test", "risk_level": "low"}'
        
        response_template = '{"steps": [{"step_id": "step1", "agent_id": "architect", "action": "test", "params": {}, "dependencies": []}], "tool_requirements": ["test"]}'
        audit_template = '{"result_status": true, "evidence_summary": "Logic Passed", "integration_reality_score": 0.9, "safe_to_finalize": true}'
        policy_template = '{"proposed_rule": "Test Rule", "reason": "Test Reason", "expected_benefit": "Improvement"}'
        strategy_template = '{"is_feasible": true, "max_attempts": 2, "consensus_required": false, "simulation_required": false}'

        self.mock_complete.side_effect = [
            MagicMock(content=strategy_template), # Strategy
            MagicMock(content=response_template), # Planning
            MagicMock(content=audit_template),    # Verification
            MagicMock(content=policy_template)    # Policy (bg)
        ]

        # 3. DB & Session Mocks
        self.mock_db = AsyncMock()
        mock_ctx = MagicMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=self.mock_db)
        mock_ctx.__aexit__ = AsyncMock()
        
        self.session_patchers = [
            patch("core.agi.central_executive.session_scope", return_value=mock_ctx),
            patch("core.agi.operational.motor_subsystem.session_scope", return_value=mock_ctx),
            patch("core.agi.adaptation.policy_engine.session_scope", return_value=mock_ctx)
        ]
        for p in self.session_patchers: p.start()

        # 4. Other Logic Patcher
        self.logic_patchers = [
            patch("memory.store.get_embedding", AsyncMock(return_value=[0.1]*1536)),
            patch("memory.store.memory_store.memory_write_gate", AsyncMock(return_value=True)),
            patch("memory.store.memory_store.save_episode", AsyncMock()),
            patch("memory.store.memory_store.get_recent", AsyncMock(return_value=[])),
            patch("api.ws_manager.ws_manager.broadcast_skill_trace", AsyncMock())
        ]
        for p in self.logic_patchers: p.start()

        self.brain = CentralExecutive()
        self.brain.agents = {
            "architect": MagicMock(execute=AsyncMock(return_value=MagicMock(raw_output="Cognitive Output")))
        }
        self.brain.motor.agents = self.brain.agents

    async def asyncTearDown(self):
        self.patcher_http.stop()
        self.patcher_orch_task.stop()
        self.patcher_orch_gen.stop()
        for p in self.session_patchers: p.stop()
        for p in self.logic_patchers: p.stop()
        
        pending = asyncio.all_tasks()
        pending = [t for t in pending if t is not asyncio.current_task()]
        if pending:
            await asyncio.wait(pending, timeout=0.1)

    async def test_unified_thought_cycle_with_reflection(self):
        """Merkezi Yürütücü Düşünce Döngüsü Testi."""
        episode = await self.brain.execute_thought_cycle("Otonom Test", source=SourceType.USER_MESSAGE)
        self.assertTrue(episode.verification.result_status)
        self.assertEqual(episode.final_output, "Cognitive Output")

    async def test_causal_failure_reflection(self):
        """Nedensel Refleksiyon testi (Hata sonrası başarı)."""
        self.mock_complete.side_effect = [
            MagicMock(content='{"max_attempts": 2, "consensus_required": false, "simulation_required": false}'),
            MagicMock(content='{"steps": [{"step_id": "s1", "agent_id": "architect", "action": "test", "params": {}}]}'),
            MagicMock(content='{"result_status": false, "evidence_summary": "Fail", "integration_reality_score": 0.2}'),
            MagicMock(content='{"links": [], "diagnostics": {"failure_reason_summary": "Bug", "root_cause_step": "s1"}}'),
            MagicMock(content='{"steps": [{"step_id": "s2", "agent_id": "architect", "action": "fix"}]}'),
            MagicMock(content='{"result_status": true, "evidence_summary": "Fixed", "integration_reality_score": 1.0, "safe_to_finalize": true}'),
            MagicMock(content='{"rule": "Fix"}')
        ]
        episode = await self.brain.execute_thought_cycle("Reflection Test", source=SourceType.USER_MESSAGE)
        self.assertTrue(episode.verification.result_status)

if __name__ == "__main__":
    unittest.main()
