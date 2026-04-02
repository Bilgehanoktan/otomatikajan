import asyncio
import logging
import json
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from core.agi.cognitive.sovereign_cortex import SovereignCortex
from core.agi.task_governance import SovereignGoal, GovernedTask, TaskStatus, TaskPlanner
from core.agi.schemas import ActionRecord, VerificationReport, EpisodeRecord

logging.basicConfig(level=logging.INFO)
_log = logging.getLogger("phase_37_verif")

async def test_recursive_meta_learning():
    _log.info("Starting Phase 37 Verification: Recursive Meta-Learning...")

    # 1. Initialize Cortex
    cortex = SovereignCortex()
    
    # 2. Create a simulated SovereignGoal (Task)
    task = SovereignGoal(
        id="t123",
        title="Meta Learning Test Project",
        status=TaskStatus.COMPLETED
    )

    # 3. Simulate a FAILED Episode Record that the mirror would return
    mock_action = ActionRecord(
        agent_id="architect",
        tool_used="architecture_draft",
        output_data="Hatalı mimari...",
        success=False
    )
    
    mock_episode = EpisodeRecord(
        episode_id="ep1",
        actions=[mock_action],
        lessons_learned=["Architect boundaries yetersiz: Fazla detaya giriyor."],
        metacognitive_score=0.5, # Above trigger threshold
        verification=VerificationReport(
            result_status=False, # Failed
            evidence_summary="Mimari standartlara uyulmadı.",
            integration_reality_score=0.2
        )
    )

    # 4. Mock dependencies to bypass real DB/Mirror calls
    # We want to jump straight to the meta-learning logic
    cortex.prompt_synth.refine_contract = AsyncMock(return_value={
        "skill": "Sistem tasarımı (İYİLEŞTİRİLMİŞ)",
        "boundaries": "Kod yazma, SADECE yüksek seviyeli şema oluştur.",
        "expected_output": "1. Şema\n2. Sınırlar"
    })

    with patch("core.agi.learning.cognitive_mirror.cognitive_mirror.reflect", return_value=mock_episode), \
         patch("core.agi.learning.memory_gate.memory_gate.evaluate_eligibility", return_value=True), \
         patch("db.session.get_db"), \
         patch("core.agi.cognitive.synaptic_cortex.synaptic_cortex.save_episode"), \
         patch("core.agi.cognitive.synaptic_cortex.synaptic_cortex.save"), \
         patch("core.agi.learning.distiller.skill_distiller.distill"):
        
        _log.info("Triggering post-task reflection on task...")
        # Simulating the actual episode that would be processed
        # Note: In the real code, _post_task_reflection takes (task, episode) or re-extracts it.
        # But based on the current sovereign_cortex.py, let's see:
        # async def _post_task_reflection(self, task: ProjectTask):
        # We need to pass the 'task' (SovereignGoal alias)
        
        try:
            # We mock the 'episode' variable that reflection would use if it was internal
            # Actually, _post_task_reflection expects a SovereignGoal (ProjectTask).
            # It usually gets the episode from the execution flow.
            # Let's adjust the test to match the signature.
            
            # Since reflect is called inside _post_task_reflection, we pass 'task'
            await cortex._post_task_reflection(task)
            
            # 5. Verify TaskPlanner update
            updated_contract = cortex.planner.dynamic_contracts.get("architect")
            if updated_contract and "İYİLEŞTİRİLMİŞ" in updated_contract["skill"]:
                _log.info("✅ SUCCESS: Architect contract refined autonomously via Meta-Learning.")
            else:
                _log.error(f"❌ FAILURE: Contract not updated or incorrect. Found: {updated_contract}")
                return

            # 6. Verify that NEW plans use the updated contract
            _log.info("Verifying that subsequent plans used the refined contract...")
            new_subtasks = cortex.planner.plan("New Project", "New Description")
            architect_task = next((st for st in new_subtasks if st.agent_id == "architect"), None)
            
            if architect_task and "İYİLEŞTİRİLMİŞ" in architect_task.prompt:
                _log.info("✅ SUCCESS: New subtask prompt contains refined instructions.")
            else:
                _log.error("❌ FAILURE: New plan used old static contract.")

        except Exception as e:
            _log.error(f"❌ Verification failed with error: {e}")
            import traceback
            _log.error(traceback.format_exc())

    _log.info("Phase 37 Verification COMPLETED.")

if __name__ == "__main__":
    asyncio.run(test_recursive_meta_learning())
