import asyncio
import uuid
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from core.agi.cognitive.sovereign_cortex import SovereignCortex
from core.agi.task_governance import SovereignGoal, GovernedTask, GovernanceStatus
from quality.output_schema import AgentOutput
from quality.reviewer import ReviewResult
from core.agi.cognitive.subconscious.metacognitive_auditor import metacognitive_auditor
from memory.retrieval import context_builder

class TestMetacognitiveLoopV39(unittest.IsolatedAsyncioTestCase):
    
    async def test_recursive_learning_cycle_v39(self):
        print("\n--- Phase 39: Metacognitive Loop Verification ---")
        
        # 1. Setup Mock DB and Cortex
        db = AsyncMock()
        cortex = SovereignCortex()
        
        # 2. Mock a task that REQUIRED REVISION
        orig_output = AgentOutput(
            agent_id="test_agent",
            summary="Initial bad output",
            decisions=["Decision 1"],
            risks=[],
            next_actions=[]
        )
        
        rev_output = AgentOutput(
            agent_id="test_agent",
            summary="Improved output after review",
            decisions=["Decision 1", "Decision 2"],
            risks=[MagicMock(description="New risk")],
            next_actions=["Action 1"]
        )
        
        review_result = ReviewResult(
            original_score=0.4,
            final_score=0.85,
            revisions=1,
            improved=True,
            final_output=rev_output,
            review_notes=["Added more detail", "Fixed logic error X"]
        )
        
        # 3. Trigger Audit
        # Mock LLM response for Lesson Distillation
        mock_lesson_json = {
            "root_cause": "Logic error X caused by omission of dependency Y",
            "countermeasure": "Always check for dependency Y in this context",
            "suggested_rule": "R-123: Verify dependency Y"
        }
        
        import json
        with patch.object(metacognitive_auditor.model_orch, "complete_task", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = MagicMock(content=f"```json\n{json.dumps(mock_lesson_json)}\n```")
            
            with patch("core.agi.cognitive.synaptic_cortex.synaptic_cortex.save_negative_lesson", new_callable=AsyncMock) as mock_save:
                await metacognitive_auditor.audit_and_learn(
                    db=db,
                    agent_id="test_agent",
                    original_output=orig_output,
                    review_result=review_result
                )
                
                # Check distillation
                self.assertTrue(mock_save.called, "Lesson should be saved to Synaptic Memory")
                args, kwargs = mock_save.call_args
                self.assertIn("Logic error X", kwargs['body'])
                print("Lesson Distillation: SUCCESS (Saved to UGC)")

        # 4. Verify Context Injection in Next Task
        mock_memories = [
            {
                "category": "negative_lesson",
                "body": "LESSON: Logic error X\nGUIDE: Always check for dependency Y",
                "score": 0.9
            }
        ]
        
        with patch.object(context_builder, "_search_memories", new_callable=AsyncMock) as mock_search:
            # First call for negative_lessons, second for general
            mock_search.side_effect = [mock_memories, []]
            
            context = await context_builder.build_context(
                agent_id="test_agent",
                task_text="Run similar task again"
            )
            
            self.assertIn("!!! ÖNEMLİ: GEÇMİŞ HATALARDAN DERSLER !!!", context)
            self.assertIn("Logic error X", context)
            print("Lesson Injection: SUCCESS (Found in Context)")

if __name__ == "__main__":
    unittest.main()
