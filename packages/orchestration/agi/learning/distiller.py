import json
from typing import Optional, Dict, Any
from packages.orchestration.agi.schemas import EpisodeRecord, SkillArtifact
from packages.llm_gateway.model_orchestrator import ModelOrchestrator
from packages.orchestration.agi.cognitive.synaptic_cortex import synaptic_cortex as memory_store
from packages.observability.logging import get_logger

_log = get_logger("agi_skill_distiller")

class SkillDistiller:
    """
    Learning Core (Katman 7): Autonomous Experience Distillation.
    Başarılı Episode kayıtlarından tekrar kullanılabilir 'Skill'ler türetir.
    """
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()

    async def distill(self, episode: EpisodeRecord, db: Any) -> Optional[SkillArtifact]:
        """
        Episode kaydını analiz eder ve genelleştirilmiş bir skill olup olamayacağına karar verir.
        """
        # SUCCESS-ONLY SKILL DISTILLATION
        if not episode.verification or not episode.verification.result_status:
           if episode.lessons_learned:
               _log.info("Episode başarısız ama dersler var. Negatif öğrenme uygulanıyor.")
           else:
               _log.info("Episode başarısız ve ders yok. Öğrenim atlanıyor.")
               return None

        if episode.verification and episode.verification.integration_reality_score < 0.4:
           _log.info("Gerçeklik puanı çok düşük. Öğrenim riskli.")
           return None

        _log.info(f"Skill damıtma başlatılıyor: {episode.problem_frame.objective if episode.problem_frame else 'Unknown'}")

        # LLM'e özet gönder
        prompt = self._build_distillation_prompt(episode)
        system_prompt = (
            "Sen bir AGI Öğrenme Çekirdeği (Learning Core) bileşenisin. "
            "Verilen görev geçmişinden (Episode), gelecekte benzer durumlarda "
            "tekrar kullanılabilecek, atomik ve yapısal bir Skill çıkartmalısın. "
            "Çıktıyı MUTLAKA geçerli bir JSON formatında ver."
        )

        try:
            response = await self.model_orch.complete_task(
                agent_role="strategist",
                prompt=prompt,
                system_prompt=system_prompt
            )
            
            skill_data = self._parse_json(response.content)
            if not skill_data:
                return None

            skill = SkillArtifact(
                skill_id=f"skill_{episode.episode_id[:8]}",
                name=skill_data.get("name", "Unnamed Skill"),
                description=skill_data.get("description", ""),
                trigger_pattern=skill_data.get("trigger_pattern", ""),
                preconditions=skill_data.get("preconditions", []),
                steps=skill_data.get("steps", []),
                tools_required=skill_data.get("tools_required", []),
                evidence_requirements=skill_data.get("evidence_requirements", []),
                failure_modes=skill_data.get("failure_modes", []),
                confidence_score=episode.verification.confidence_adjusted or 0.8
            )

            # Hafızaya kaydet
            await memory_store.save_skill(db, {
                "skill_id": skill.skill_id,
                "name": skill.name,
                "description": skill.description,
                "trigger_pattern": skill.trigger_pattern,
                "preconditions": skill.preconditions,
                "steps": skill.steps,
                "tools_required": skill.tools_required,
                "metadata": {
                    "source_episode": episode.episode_id,
                    "reality_score": episode.verification.integration_reality_score
                }
            })
            
            _log.info(f"Otonom Skill Kaydedildi: {skill.name}")
            return skill

        except Exception as e:
            _log.error(f"Skill distillation hatası: {e}")
            return None

    def _build_distillation_prompt(self, ep: EpisodeRecord) -> str:
        actions_summary = "\n".join([
            f"- Adım: {a.tool_used} | Başarı: {a.success} | Özet: {str(a.output_data)[:200]}"
            for a in ep.actions
        ])
        
        return f"""
        GÖREV HEDEFİ: {ep.problem_frame.objective if ep.problem_frame else 'N/A'}
        GÖREV TİPİ: {ep.problem_frame.task_type.value if ep.problem_frame else 'N/A'}
        
        UYGULANAN ADIMLAR:
        {actions_summary}
        
        SONUÇ: {str(ep.final_output)[:500]}
        
        Lütfen bu deneyimi gelecekteki görevler için bir 'Skill' (Yetenek) olarak yapılandır.
        JSON formatında şu alanları içermelidir:
        - name: Skill ismi
        - description: Ne işe yarar?
        - trigger_pattern: Hangi tür inputlarda tetiklenmeli?
        - preconditions: Çalışması için ne lazım (örn: node kurulu olmalı)
        - steps: Bu yeteneğin mantıksal adımları
        - tools_required: Gerekli araçlar listesi
        - evidence_requirements: Başarıyı doğrulamak için neye bakılmalı?
        - failure_modes: Olası hata durumları
        """

    def _parse_json(self, content: str) -> Optional[Dict[str, Any]]:
        try:
            # Markdown code block temizleme
            clean = content.strip()
            if "```json" in clean:
                clean = clean.split("```json")[1].split("```")[0].strip()
            elif "```" in clean:
                clean = clean.split("```")[1].split("```")[0].strip()
            return json.loads(clean)
        except Exception:
            return None

# --- Singleton ---
skill_distiller = SkillDistiller()
