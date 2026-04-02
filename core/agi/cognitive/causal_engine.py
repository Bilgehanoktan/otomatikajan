import json
from typing import Optional, List, Dict, Any
from core.agi.schemas import EpisodeRecord, CausalGraph, CausalLink
from llm.model_orchestrator import ModelOrchestrator
from observability.logging import get_logger

_log = get_logger("agi_causal_engine")

class CausalEngine:
    """
    Cognitive Core (Katman 3): Causal Reasoning.
    Eylemler ve sonuçlar arasındaki 'Neden-Sonuç' (Causality) ilişkilerini haritalandırır.
    """
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()

    async def analyze_episode(self, episode: EpisodeRecord, depth: int = 1) -> CausalGraph:
        """
        Bir bölümün (Episode) nedensel yapısını analiz eder. 
        Depth > 1 ise recursive kök neden analizi yapar.
        """
        _log.info(f"Nedensellik analizi başlatılıyor: {episode.episode_id} (Depth: {depth})")
        
        prompt = self._build_analysis_prompt(episode, depth)
        system_prompt = (
            "Sen bir AGI Nedensel Akıl Yürütme (Causal Reasoning) bileşenisin. "
            "Görevin, yapılan eylemler ve alınan sonuçlar arasındaki bağıntıları kurmaktır. "
            "Özellikle 'Counterfactual Thinking' (Karşı olgusal düşünce) kullanarak 'Eğer X olmasaydı Y olur muydu?' sorusunu sor."
        )

        try:
            response = await self.model_orch.complete_task(
                agent_role="strategist",
                prompt=prompt,
                system_prompt=system_prompt
            )
            
            causal_data = self._parse_json(response.content)
            links = []
            for link in causal_data.get("links", []):
                links.append(CausalLink(
                    cause_id=link.get("cause"),
                    effect_id=link.get("effect"),
                    relationship_type=link.get("type"),
                    confidence=link.get("confidence", 0.8),
                    metadata=link.get("metadata", {})
                ))
            
            # --- [FIX-10] Faz 21: Recursive Diagnostics — Artık Gerçekten Çalışıyor ---
            diagnostics = causal_data.get("diagnostics", {})
            if depth > 1 and episode.verification and not episode.verification.result_status:
                _log.info(f"[CAUSAL] Yansımalı (Reflective) Analiz tetikleniyor: Depth {depth-1}")
                drill_links = await self._drill_down_action_causes(episode, depth - 1)
                links.extend(drill_links)
                _log.info(f"[CAUSAL] Drill-down analiz tamamlandı: {len(drill_links)} ek nedensel bağ bulundu.")
            
            graph = CausalGraph(
                links=links,
                nodes_metadata=diagnostics
            )
            _log.info(f"Nedensel grafik oluşturuldu: {len(links)} bağ.")
            return graph

        except Exception as e:
            _log.error(f"Causal analysis hatası: {e}")
            return CausalGraph()

    async def _drill_down_action_causes(self, episode: EpisodeRecord, depth: int) -> List[CausalLink]:
        """
        [FIX-10] Recursive derinlemesine nedensel analiz.
        Episode'daki her başarısız action için LLM'e ayrı ayrı soruyor: 
        'Bu adım neden başarısız oldu?'
        """
        extra_links: List[CausalLink] = []
        failed_actions = [a for a in episode.actions if not a.success]
        
        if not failed_actions:
            # Sistem başarısız oldu ama belirli bir action başarısız değil
            # Genel verification failure'a bak
            failed_actions = episode.actions[-1:] if episode.actions else []

        for action in failed_actions[:3]:  # En fazla 3 action incele (token tasarrufu)
            prompt = f"""
            Başarısız eylem analizi:
            Ajan: {action.tool_used}
            Giriş: {str(action.input_data)[:200]}
            Çıktı: {str(action.output_data)[:200]}
            Hatalar: {action.errors}

            'Kademeli Nedensellik' (Kaba Neden Analizi) yap:
            Bu eylemin neden başarısız olduğunun olasi 3 nedenini sırala.
            JSON listesi döndür:
            [
              {{
                "cause": "ne yol açtı",
                "effect": "{action.action_id}_failure",
                "type": "causes_failure",
                "confidence": 0.85,
                "metadata": {{"action_id": "{action.action_id}", "depth": {depth}}}
              }}
            ]
            """
            try:
                resp = await self.model_orch.complete_task(
                    agent_role="critic",
                    prompt=prompt,
                    system_prompt="AGI Nedensel Analiz uzmanı olarak başarısızlıkların kök nedenlerini bulursun."
                )
                import re
                import json as _json
                m = re.search(r'\[.*\]', resp.content, re.DOTALL)
                if m:
                    raw = _json.loads(m.group())
                    for item in raw:
                        extra_links.append(CausalLink(
                            cause_id=str(item.get("cause", "unknown")),
                            effect_id=str(item.get("effect", action.action_id)),
                            relationship_type=item.get("type", "causes_failure"),
                            confidence=float(item.get("confidence", 0.7)),
                            metadata=item.get("metadata", {})
                        ))
            except Exception as drill_err:
                _log.warning(f"[CAUSAL] Drill-down hatası action {action.action_id}: {drill_err}")
        
        return extra_links

    async def simulate_counterfactual(self, episode: EpisodeRecord, alternative_action: str) -> Dict[str, Any]:
        """
        [Mental Sandbox] - Bir eylem farklı olsaydı sonucun nasıl değişeceğini simüle eder.
        """
        _log.info(f"Counterfactual simülasyon başlatılıyor: {alternative_action}")
        
        prompt = f"""
        BÖLÜM GEÇMİŞİ:
        Girdi: {episode.problem_frame.objective if episode.problem_frame else 'Unknown'}
        Yapılan Eylemler: {json.dumps([a.tool_used for a in episode.actions])}
        Sonuç: {'Başarılı' if episode.verification and episode.verification.result_status else 'Başarısız'}
        
        EĞER ŞU EYLEM YAPILSAYDI: {alternative_action}
        
        Lütfen bu değişikliğin tüm süreci nasıl etkileyeceğini ve başarı ihtimalini nasıl değiştireceğini tahmin et.
        Yanıtı JSON formatında ver:
        {{
            "predicted_outcome": "Başarı|Başarısızlık",
            "impact_analysis": "Olası değişimlerin özeti",
            "confidence": 0.0-1.0
        }}
        """
        
        try:
            resp = await self.model_orch.complete_task(
                agent_role="strategist",
                prompt=prompt,
                system_prompt="Sen bir Mental Sandbox simülatörüsün."
            )
            return self._parse_json(resp.content)
        except Exception as e:
            return {"error": str(e)}

    def _build_analysis_prompt(self, episode: EpisodeRecord, depth: int = 1) -> str:
        actions_str = "\n".join([
            f"- {a.step_id}: Tool: {a.tool_used} | Success: {a.success} | Output: {str(a.output_data)[:200]}"
            for a in episode.actions
        ])
        
        return f"""
        HEDEF: {episode.problem_frame.objective if episode.problem_frame else 'Unknown'}
        
        EYLEMLER:
        {actions_str}
        
        VERİFİKASYON SONUCU:
        {episode.verification.evidence_summary if episode.verification else 'No verification'}
        
        Lütfen bu veriler ışığında nedensel bağıntıları kur. 
        Hangi adım hangi sonucun gerçek nedenidir? Eğer hata varsa, "Kök Neden" (Root Cause) hangisidir?
        
        JSON formatında yanıt ver:
        {{
            "links": [
                {{ "cause": "step_id_or_input", "effect": "step_id_or_result", "type": "triggers|causes_failure|enables", "confidence": 0.9 }}
            ],
            "diagnostics": {{
                "root_cause_step": "step_id",
                "failure_reason_summary": "Kısa özet"
            }}
        }}
        """

    def _parse_json(self, content: str) -> Dict[str, Any]:
        try:
            import re
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception:
            pass
        return {}

# Singleton
causal_engine = CausalEngine()
