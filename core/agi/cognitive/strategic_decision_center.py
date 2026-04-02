import json
import re
import asyncio
from typing import List, Dict, Any, Optional
from observability.logging import get_logger
from llm.model_orchestrator import ModelOrchestrator
from core.agi.schemas import (
    ProblemFrame, ContextPackage, ExecutionPlan, PlanStep, RiskLevel, AffectiveState
)
from core.agi.cognitive.foresight_cortex import foresight_cortex
from core.agi.cognitive.motivation_engine import motivation_engine

_log = get_logger("agi_strategic_decision")

class StrategicDecisionCenter:
    """
    Bilişsel Çekirdek - Stratejik Karar Merkezi (Strategic Decision Center).
    Faz 12.2 Hardening: Öngörülü Stratejik Hizalama ve Durum Farkındalığı.
    Birden fazla plan varyantı üretir, ForesightCortex ile simüle eder ve 
    en yüksek 'Alignement' skoruna sahip olanı seçer.
    """
    def __init__(self, model_orch: ModelOrchestrator):
        self.model_orch = model_orch

    async def decide(self, frame: ProblemFrame, context: ContextPackage) -> ExecutionPlan:
        """
        Daha derin bir akıl yürütme ile en iyi planı seç.
        """
        _log.info(f"[DECISION] Stratejik karar süreci başlatıldı: {frame.objective}")
        
        # Faz 28: Duygusal Durum (Affective State) Alımı
        aff_state = context.affective_context or motivation_engine.current_state
        _log.info(f"[DECISION] Mood: {aff_state.persistence_policy} | Stress: {aff_state.internal_stress:.2f}")
        # Not: Tek bir LLM çağrısında 3 farklı 'strateji' (Safe, standard, optimal) isteyebiliriz.
        # Bu hem hız kazandırır hem de karşılaştırma yapmayı sağlar.
        
        variants = await self._generate_plan_variants(frame, context)
        if not variants:
             return self._get_fallback_plan(frame)

        # 2. Her planı ForesightCortex ile Simüle et (Parallel Simulation)
        simulation_tasks = [foresight_cortex.simulate_plan(v) for v in variants]
        sim_results = await asyncio.gather(*simulation_tasks)

        # 3. Skorlama ve Seçim (Affective Weighting Entegrasyonu)
        best_plan = None
        best_score = -1.0
        
        # Duygusal Ağırlıklar (Affective Weights) - Faz 12.3 Hardening
        # Stres yüksekse Caution %30 ek puan alır.
        # Merak yüksekse Optimal/Aggressive %20 ek puan alır.
        caution_boost = 0.3 if aff_state.internal_stress > 0.6 else 0.0
        curiosity_boost = 0.2 if aff_state.motivation_level > 0.8 else 0.0

        for i, plan in enumerate(variants):
            sim = sim_results[i]
            base_score = sim.get("strategic_alignment_score", 0.5)
            risk_penalty = len(sim.get("predicted_risks", [])) * 0.1
            
            # Dinamik Ağırlıklandırma
            final_score = base_score - risk_penalty
            
            variant_name = "standard"
            if "cautious" in str(plan.goal).lower():
                final_score += caution_boost
                variant_name = "cautious"
            elif "optimal" in str(plan.goal).lower() or "aggressive" in str(plan.goal).lower():
                final_score += curiosity_boost
                variant_name = "optimal"

            _log.info(f"[DECISION] Variant {i+1} ({variant_name}) Final Score: {final_score:.2f} (Base: {base_score})")
            
            if final_score > best_score:
                best_score = final_score
                best_plan = plan
                best_plan.evaluated_alternatives = [
                    {"variant_index": j, "score": sim_results[j].get("strategic_alignment_score")} 
                    for j in range(len(variants))
                ]
                best_plan.workspace["mood_selection"] = variant_name

        return best_plan

    async def _generate_plan_variants(self, frame: ProblemFrame, context: ContextPackage) -> List[ExecutionPlan]:
        """Birden fazla plan seçeneği üretir."""
        prompt = self._build_strategic_prompt(frame, context)
        
        try:
            response = await self.model_orch.complete(
                [{"role": "user", "content": prompt}],
                preferred_agent="architect"
            )
            
            # JSON array bekliyoruz: [{"goal": "...", "steps": [...]}, ...]
            match = re.search(r'\[.*\]', response, re.DOTALL)
            if not match:
                # Tek bir JSON objesi geldiyse listeye çevir
                match = re.search(r'\{.*\}', response, re.DOTALL)
                if match:
                    raw_variants = [json.loads(match.group())]
                else:
                    return []
            else:
                raw_variants = json.loads(match.group())

            plans = []
            for v_data in raw_variants:
                steps = [PlanStep(**s) for s in v_data.get("steps", [])]
                plans.append(ExecutionPlan(
                    goal=v_data.get("goal", frame.objective),
                    steps=steps,
                    tool_requirements=v_data.get("tool_requirements", []),
                    confidence_estimate=v_data.get("confidence_estimate", 0.8),
                    estimated_risk=RiskLevel(v_data.get("estimated_risk", frame.risk_level.value))
                ))
            return plans

        except Exception as e:
            _log.error(f"[DECISION] Plan üretimi başarısız: {e}")
            return []

    def _build_strategic_prompt(self, frame: ProblemFrame, context: ContextPackage) -> str:
        # Integrity Awareness (Durum Farkındalığı)
        integrity = context.integrity_status
        mode_str = f"Sistem Durumu: {integrity.get('mode', 'nominal').upper()}"
        if integrity.get("degraded_components"):
            mode_str += f" (Kısıtlı: {', '.join(integrity['degraded_components'])})"

        # Synapse Lessons
        lessons_text = "\n".join([f"- [{m['category']}]: {m['body']}" for m in context.synapse_lessons]) if context.synapse_lessons else "Ders bulunamadı."

        prompt = f"""
        ### SYSTEM STATUS: {mode_str}
        Eğer durum NOMINAL değilse, planlarını sistem kısıtlamalarına göre düzenle (Örn: DB/API sorunluysa alternatif yollar bul).
        
        HEDEF: {frame.objective}
        
        ### COGNITIVE MEMORY (SYNAPSE):
        {lessons_text}
        
        ### GÖREV:
        Lütfen bu hedef için 3 farklı PLAN VARYANTI üret (JSON listesi olarak):
        1. 'Standard': En dengeli yol.
        2. 'Cautious': Maksimum doğrulama, minimum risk.
        3. 'Optimal': En hızlı ve verimli yol.
        
        Format (SADECE JSON Listesi):
        [
          {{
            "goal": "Kısa hedef açıklaması",
            "steps": [ {{ "step_id": "s1", "agent_id": "architect", "action": "...", "params": {{}} }} ],
            "estimated_risk": "low/medium/high"
          }}
        ]
        """
        return prompt

    def _get_fallback_plan(self, frame: ProblemFrame) -> ExecutionPlan:
        return ExecutionPlan(
            goal=frame.objective,
            steps=[PlanStep(step_id="fallback", agent_id="architect", action="execute")],
            estimated_risk=frame.risk_level
        )
