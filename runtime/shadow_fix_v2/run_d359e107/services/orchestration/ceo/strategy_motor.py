import logging
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from services.observability.logging import get_logger
from libs.llm.model_orchestrator import ModelOrchestrator
from libs.db.session import session_scope
from libs.db.models import SovereignGoal, Project

logger = get_logger("ceo.strategy_motor")

class CEOStrategyMotor:
    """
    Sovereign AGI Strategy Formulation Engine.
    Synthesizes long-term roadmaps and North Star goals from system audit data.
    """

    def __init__(self, model_orch: ModelOrchestrator):
        self.model_orch = model_orch

    @staticmethod
    def _normalize_priority(value: Any) -> int:
        if isinstance(value, (int, float)):
            return max(0, min(100, int(value)))

        text = str(value or "P1").strip().upper()
        priority_map = {"P0": 100, "P1": 80, "P2": 50, "P3": 20}
        if text in priority_map:
            return priority_map[text]

        try:
            return max(0, min(100, int(float(text))))
        except ValueError:
            return priority_map["P1"]

    async def formulate_new_goals(self, audit_findings: List[Dict[str, Any]]) -> List[SovereignGoal]:
        """
        Denetim bulgularını analiz ederek sistemdeki 'bilişsel boşlukları' dolduracak 
        yeni North Star hedefleri önerir ve oluşturur.
        """
        if not audit_findings:
            return []

        prompt = f"""
        Aşağıdaki Sovereign AGI sistem denetim bulgularını analiz et. 
        Sistemin otonomisini, verimliliğini veya güvenliğini artıracak 1 adet yeni 'North Star' hedefi (SovereignGoal) tanımla.
        
        BULGULAR:
        {audit_findings}
        
        Yanıt Formatı (JSON):
        {{
            "title": "Hedef Başlığı",
            "description": "Detaylı açıklama ve vizyon",
            "priority": "P0-P3",
            "kpis": {{"key_metric": "target_value"}}
        }}
        """
        
        try:
            response = await self.model_orch.complete_task(
                agent_role="ceo",
                prompt=prompt,
                system_prompt="Sen bir Sovereign AGI CEO'susun. Sistemin uzun vadeli vizyonunu ve hedeflerini belirlersin."
            )

            import json
            import re

            content = response.content if hasattr(response, 'content') else str(response)
            json_match = re.search(r'\{.*\}', content, re.DOTALL)

            if json_match:
                data = json.loads(json_match.group())

                async with session_scope() as db:
                    new_goal = SovereignGoal(
                        id=uuid.uuid4(),
                        title=data.get("title", "Otonom Sentezlenen Hedef"),
                        vision_statement=data.get("description", ""),
                        priority=self._normalize_priority(data.get("priority", "P1")),
                        kpis=data.get("kpis", {}),
                        status="active"
                    )
                    db.add(new_goal)
                    await db.commit()

                logger.info(f"👔 CEO Strategy Motor: New Strategic Goal Synthesized & Saved: {new_goal.title}")
                return [new_goal]

            logger.warning(f"👔 CEO Strategy Motor: Failed to parse JSON from: {content[:50]}...")
            return []
        except Exception as e:
            logger.error(f"Strategy formulation failed: {e}")
            return []

    async def derive_projects_from_goal(self, goal: SovereignGoal) -> List[Project]:
        """
        Bir üst hedefi gerçekleştirilebilir mikro-projelere böler.
        """
        # Hedefin description'ını analiz et ve proje listesi çıkar
        logger.info(f"👔 CEO Strategy Motor: Deriving infrastructure projects for '{goal.title}'")
        return []
