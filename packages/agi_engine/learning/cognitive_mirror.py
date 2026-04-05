import json
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from core.agi.schemas import EpisodeRecord, VerificationReport, ActionRecord
from llm.model_orchestrator import ModelOrchestrator
from observability.logging import get_logger

_log = get_logger("cognitive_mirror")

class CognitiveMirror:
    """
    Bilişsel Yansıma Çekirdeği (Metacognition Core - Phase 27).
    Görevin tamamlanmasının ardından, süreci 'dışarıdan' bir gözle (evaluator)
    inceler ve bilişsel dersler çıkarır.
    """
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()

    async def reflect(self, episode: EpisodeRecord) -> EpisodeRecord:
        """
        Episode kaydını analiz eder, dersler çıkarır ve kaydı günceller.
        """
        _log.info(f"Bilişsel yansıma başlatılıyor. Episode: {episode.episode_id}")
        
        # 1. Ham veriyi hazırla
        prompt = self._build_reflection_prompt(episode)
        system_prompt = (
            "Sen bir 'Sovereign AGI Bilişsel Denetçi' (Metacognitive Auditor) birimisin. "
            "Görevin, tamamlanmış bir görev akışını (Episode) inceleyerek; "
            "stratejik hataları, kök nedenleri, başarılı desenleri ve çıkarılabilecek otonom dersleri belirlemektir. "
            "Dürüst, eleştirel ve teknik bir dille analiz yapmalısın. "
            "Yanıtını MUTLAKA JSON formatında ver."
        )

        try:
            response = await self.model_orch.complete_task(
                agent_role="critic",
                prompt=prompt,
                system_prompt=system_prompt
            )
            
            reflection_data = self._parse_json(response.content)
            if not reflection_data:
                _log.warning("Bilişsel yansıma verisi çözümlenemedi.")
                return episode

            # 2. Episode kaydını güncelle
            episode.lessons_learned = reflection_data.get("lessons", [])
            episode.skill_candidates = reflection_data.get("potential_skills", [])
            episode.metacognitive_score = reflection_data.get("reasoning_quality_score", 0.5)
            
            # Drift/Sapma kontrolü (Planlanan vs Gerçekleşen)
            if reflection_data.get("detected_drift", False):
                episode.internal_drift_detected = True
                _log.warning(f"Bilişsel sapma tespit edildi: {reflection_data.get('drift_reason')}")

            _log.info(f"Bilişsel yansıma tamamlandı. Skor: {episode.metacognitive_score}")
            return episode

        except Exception as e:
            _log.error(f"Reflection hatası: {e}")
            episode.lessons_learned.append(f"Reflection Error: {str(e)}")
            return episode

    def _build_reflection_prompt(self, ep: EpisodeRecord) -> str:
        status_text = "BAŞARILI" if ep.verification and ep.verification.result_status else "BAŞARISIZ"
        
        actions_log = "\n".join([
            f"Adım {idx+1} ({a.tool_used}): {'✓' if a.success else '✗'} - {str(a.output_data)[:200]}"
            for idx, a in enumerate(ep.actions)
        ])
        
        prompt = f"""
        # EPISODE ÖZETİ ({ep.episode_id})
        DURUM: {status_text}
        HEDEF: {ep.problem_frame.objective if ep.problem_frame else 'N/A'}
        RİSK SEVİYESİ: {ep.problem_frame.risk_level.value if ep.problem_frame else 'N/A'}
        
        # EYLEMLER VE ÇIKTILAR:
        {actions_log}
        
        # DOĞRULAMA RAPORU:
        {ep.verification.evidence_summary if ep.verification else 'Rapor yok'}
        
        # ANALİZ TALEBİ:
        1. Bu görevdeki en kritik başarı veya başarısızlık faktörü (Kök Neden) neydi?
        2. Plan ile uygulama arasında bir sapma (Drift) oldu mu?
        3. Bir sonraki seferde neyi farklı yapmalısın? (Dersler)
        4. Bu tecrübeden otonom bir 'Skill' türer mi?
        5. Bilişsel muhakeme kalitesini 0.0 ile 1.0 arasında puanla.

        Lütfen şu JSON formatında yanıtla:
        {{
          "root_cause": "...",
          "lessons": ["ders 1", "ders 2"],
          "potential_skills": ["skill_adi_1"],
          "detected_drift": true/false,
          "drift_reason": "...",
          "reasoning_quality_score": 0.0-1.0
        }}
        """
        return prompt

    def _parse_json(self, content: str) -> Optional[Dict[str, Any]]:
        try:
            clean = content.strip()
            if "```json" in clean:
                clean = clean.split("```json")[1].split("```")[0].strip()
            elif "```" in clean:
                clean = clean.split("```")[1].split("```")[0].strip()
            return json.loads(clean)
        except Exception:
            return None

# Singleton
cognitive_mirror = CognitiveMirror()
