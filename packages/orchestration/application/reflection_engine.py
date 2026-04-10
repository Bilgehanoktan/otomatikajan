import logging
import asyncio
from dataclasses import asdict
from typing import Any, Dict, List, Optional
from packages.observability.logging import get_logger
from packages.orchestration.domain.models import ProjectTask, TaskStatus
from packages.orchestration.agi.schemas import EpisodeRecord, ActionRecord, VerificationReport, ProblemFrame, TaskType, RiskLevel

_log = get_logger("agi_reflection_engine")

class ReflectionEngine:
    def __init__(self, affective_core):
        self.affective = affective_core

    async def reflect_on_task(self, task: ProjectTask):
        from packages.orchestration.agi.learning.cognitive_mirror import cognitive_mirror
        from packages.orchestration.agi.learning.memory_gate import memory_gate
        from packages.orchestration.agi.learning.distiller import skill_distiller
        from packages.orchestration.agi.learning.wisdom_synthesizer import wisdom_synthesizer
        from packages.orchestration.agi.cognitive.synaptic_cortex import synaptic_cortex
        from packages.persistence.session import get_db

        try:
            episode = EpisodeRecord(
                episode_id=task.id, 
                problem_frame=ProblemFrame(task_type=TaskType.OPERATION, objective=task.title, risk_level=RiskLevel.MEDIUM), 
                final_output=task.report
            )
            for st in task.subtasks:
                episode.actions.append(ActionRecord(
                    step_id=st.id, 
                    agent_id=st.agent_id, 
                    tool_used="velocity_engine", 
                    output_data=st.result, 
                    success=(st.status == TaskStatus.COMPLETED), 
                    duration_s=getattr(st, "duration_s", 0.0)
                ))
            
            reflected_episode = await cognitive_mirror.reflect(episode)
            is_eligible = await memory_gate.evaluate_eligibility(reflected_episode)
            if not is_eligible: return

            async with get_db() as db:
                await synaptic_cortex.save_thought_thread(db, f"Task '{task.title}' completed.", context_id="global")
                # More persistence logic...
            
            _log.info(f"[REFLECTION] Cognitive reflection completed for {task.id}")
            asyncio.create_task(wisdom_synthesizer.synthesize_from_task(task))
            
        except Exception as e:
            _log.error(f"[REFLECTION] Reflection error: {e}")
