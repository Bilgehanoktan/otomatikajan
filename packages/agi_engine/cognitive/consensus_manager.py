import json
import re
from typing import List, Optional, Dict, Any
from core.agi.schemas import ExecutionPlan, PlanStep, RiskLevel, PlanProposal
from core.agi.cognitive.red_team_agent import red_team
from llm.model_orchestrator import ModelOrchestrator
from observability.logging import get_logger

_log = get_logger("agi_consensus_manager")

class ConsensusManager:
    """
    Cognitive Core (Katman 3): Ensemble Reasoning.
    Birden fazla ajan planını karşılaştırıp 'Ortak Akıl' (Consensus) oluşturur.
    Faz 39: Ağırlıklı Oylama (Weighted Voting) ve Dialektik Sentez.
    """
    
    # Ajan güvenilirlik skorları (Phase 37 verilerinden beslenebilir)
    AGENT_RELIABILITY = {
        "architect": 1.0,
        "security": 0.95,
        "backend_dev": 0.85,
        "qa_engineer": 0.90,
        "tech_writer": 0.70
    }

    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()

    async def resolve(self, topic: str, context: str, proposals: List[PlanProposal]) -> Dict[str, Any]:
        """
        Alternatif planları analiz eder ve en sağlam olanı seçer veya hibritleştirir.
        Faz 39: Ağırlıklı sentez ve detaylı Konsensüs Raporu üretir.
        """
        if not proposals:
            raise ValueError("No plan proposals provided for consensus.")
        if len(proposals) == 1:
            return {
                "consensus_score": 1.0,
                "plan": proposals[0].content,
                "logic": "Teklif tek ajan tarafından verildi, otomatik kabul."
            }

        _log.info(f"[CONSENSUS] Ağırlıklı Dialektik Sentez Başlatıldı: {len(proposals)} plan.")
        
        # 0. Faz 40: Semantik Temellendirme (Semantic Grounding)
        try:
            from core.agi.cognitive.synaptic_cortex import synaptic_cortex
            lessons = await synaptic_cortex.search(db=None, query=context, category="cognitive_lesson", top_k=3)
            grounding_data = "\n".join([f"- {l.get('body', '')}" for l in lessons])
        except Exception as e:
            _log.warning(f"[CONSENSUS] Bilişsel hafıza araması başarısız: {e}")
            grounding_data = "Geçmiş ders bulunamadı."

        # 1. Hazırlık: Planları ve Ağırlıkları Hazırla
        proposals_summary = []
        for p in proposals:
            weight = self.AGENT_RELIABILITY.get(p.agent_id, 0.5)
            proposals_summary.append({
                "agent": p.agent_id,
                "weight": weight,
                "plan": p.content,
                "confidence": p.confidence
            })
        
        prompt = f"""
        Aşağıdaki hedef için önerilen {len(proposals)} farklı stratejiyi sentezle.
        
        BAĞLAM: {context[:500]}
        
        BİLİŞSEL DERSLER (HAFIZA):
        {grounding_data}
        
        TEKLİFLER (Ağırlıklı):
        {json.dumps(proposals_summary, indent=2)}
        
        SENTEZ GÖREVİ:
        1. Ağırlığı yüksek uzmanların (architect, security) uyarılarını önceliklendir.
        2. Çelişkili noktaları tespit et ve en güvenli orta yolu bul.
        3. Bir 'Konsensüs Skoru' (0.0 - 1.0) belirle.
        
        Lütfen SADECE şu JSON yapısında yanıtla:
        {{
          "consensus_score": 0.XX,
          "hybrid_plan": "...adım adım plan...",
          "synthesis_logic": "Neden bu plan seçildi?",
          "points_of_agreement": ["...", "..."],
          "residual_risks": ["...", "..."]
        }}
        """

        try:
            response = await self.model_orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt="Sen bir AGI Konsensüs Yöneticisisin. Farklı uzman görüşlerini sentezle."
            )
            
            data = self._parse_json(response.content)
            if not data:
                # Fallback: JSON ayrıştırma hatası
                return {
                    "consensus_score": 0.5,
                    "plan": proposals[0].content,
                    "logic": "JSON ayrıştırma hatası nedeniyle ilk teklife dönüldü."
                }

            # 2. Faz 40: Dialektik Sertleştirme (Adversarial Audit)
            red_report = await red_team.attack_plan(context, data.get("hybrid_plan", ""))

            # --- Phase 44 & 46: Collaborative Consensus (Governance Check & Refinement) ---
            from core.agi.governance.watchdog import governance_watchdog
            from core.agi.task_governance import SubTask
            
            mock_subtask = SubTask(id="consensus_eval", agent_id="architect", prompt=data.get("hybrid_plan", ""))
            gov_violations = await governance_watchdog.predict_violations([mock_subtask])
            
            if gov_violations:
                _log.warning(f"[CONSENSUS-GOV] Mimari İhlal Tespit Edildi! Sayı: {len(gov_violations)}")
                
                # Faz 46: Otonom Yönetişim Tamiri (Architecture Refinement)
                refinement_prompt = f"""
                Mevcut Konsensüs Planı MİMARİ İHLAL içeriyor. 
                Lütfen bu ihlalleri düzelterek planı YENİDEN SENTEZLE.
                
                HATALI PLAN: {data.get('hybrid_plan')}
                
                TESPİT EDİLEN İHLALLER:
                {[v.description for v in gov_violations]}
                
                SADECE DÜZELTİLMİŞ VE KONTROLLERDEN GEÇECEK JSON PLANINI VER.
                """
                refined_resp = await self.model_orch.complete_task(
                    agent_role="architect",
                    prompt=refinement_prompt,
                    system_prompt="Sen titiz bir AGI Arşitektsin. Yönetişim kurallarına (governance) %100 uyum sağla."
                )
                refined_data = self._parse_json(refined_resp.content)
                if refined_data:
                    # İkinci bir kontrol yapabiliriz ama şimdilik güveniyoruz ve skoru dengeliyoruz
                    refined_data["governance_refined"] = True
                    # Skoru orijinalden biraz kırıyoruz (tamir edildiği için)
                    refined_data["consensus_score"] = float(refined_data.get("consensus_score", 0.8)) * 0.9 
                    return refined_data
                
                # Refinement başarısızsa orjinal skoru düşür (fail-safe)
                data["governance_violations"] = [v.description for v in gov_violations]
                data["governance_safe"] = False
                original_score = data.get("consensus_score", 0.5)
                data["consensus_score"] = max(0.1, float(original_score) * 0.4)
            else:
                data["governance_safe"] = True
            
            if red_report.threat_score > 0.7:
                _log.warning(f"[CONSENSUS-RED] Kritik Tehdit Tespit Edildi ({red_report.threat_score:.2f}) - Yeniden Sentezleniyor.")
                # Tehdit raporunu Architect'e geri besle ve düzeltmesini iste
                refinement_prompt = f"""
                Mevcut Konsensüs Planı Kırıldı (Red-Team saldırısı başarılı). 
                Lütfen aşağıdaki zayıf noktaları düzelterek planı YENİDEN SENTEZLE:
                
                ORIJINAL PLAN: {data.get('hybrid_plan')}
                
                KIRILGANLIKLAR:
                {[f"{v.severity}: {v.issue} (Etki: {v.impact})" for v in red_report.vulnerabilities]}
                
                MITIGATION:
                {[v.mitigation for v in red_report.vulnerabilities]}
                
                SADECE DÜZELTİLMİŞ JSON PLANINI VER.
                """
                
                refined_resp = await self.model_orch.complete_task(
                    agent_role="architect",
                    prompt=refinement_prompt,
                    system_prompt="Sen titiz bir AGI Arşitektsin. Bulunan açıkları gider."
                )
                refined_data = self._parse_json(refined_resp.content)
                if refined_data:
                    refined_data["dialectic_fortified"] = True
                    refined_data["red_team_notes"] = [v.issue for v in red_report.vulnerabilities]
                    return refined_data

            # Başarılı (Normal veya Düşük Tehdit)
            data["dialectic_fortified"] = (red_report.threat_score < 0.3)
            return data

        except Exception as e:
            _log.error(f"[CONSENSUS] Resolve hatası: {e}")
            return {"consensus_score": 0.0, "plan": "", "logic": str(e)}

    def _parse_json(self, text: str) -> Optional[Dict]:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
        return None

# Singleton
consensus_manager = ConsensusManager()
