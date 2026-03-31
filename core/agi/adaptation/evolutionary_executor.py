import json
from slugify import slugify
from typing import Optional, Dict, Any, List
from core.agi.schemas import EpisodeRecord, CausalGraph
from llm.model_orchestrator import ModelOrchestrator
from core.agi.security.audit_gate import AuditGate
from observability.logging import get_logger

_log = get_logger("agi_evolution_executor")

class EvolutionaryExecutor:
    """
    Cognitive Core (Katman 7): Recursive Self-Optimization.
    Sistemin kendi kod tabanını (ajanlarını veya yardımcılarını) otonom olarak 
    iyileştiren ve refaktör eden birim.
    """
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()
        self.audit = AuditGate(self.model_orch)

    async def consider_evolution(self, episode: EpisodeRecord, causal_graph: CausalGraph):
        """
        Bir epizot sonrası evrim ihtiyacını değerlendirir.
        Özellikle başarısızlık durumlarında tetiklenir.
        """
        if episode.verification and episode.verification.result_status:
            return # Başarılıysa evrim acil değil
            
        root_cause = causal_graph.nodes_metadata.get("root_cause_step")
        if not root_cause:
            return
            
        _log.info(f"Otonom Evrim Analizi Tetiklendi. Root Cause: {root_cause}")
        
        # 1. İyileştirme Fırsatı (Improvement Opportunity) Tanımla
        prompt = f"""
        ŞU HATA ADIMI ANALİZ EDİLDİ: {root_cause}
        HATA ÖZETİ: {causal_graph.nodes_metadata.get('failure_reason_summary')}
        
        Lütfen bu hatayı kalıcı olarak önleyebilecek bir kod iyileştirmesi önerisi üret.
        Yanıtı JSON formatında ver:
        {{
            "opportunity_id": "unique_slug",
            "title": "Kısa başlık",
            "target_file": "relative/path/to/file.py",
            "reasoning": "Neden bu değişiklik gerekiyor?",
            "proposed_logic": "Yeni mantık açıklaması"
        }}
        """
        
        try:
            resp = await self.model_orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt="Sen bir AGI Sistemsel Mimarsın. Kendi hatalarından kod iyileştirme planı çıkarırsın."
            )
            opportunity = json.loads(resp.content)
            
            # 2. Yama (Patch) Sentezle (Faz 23)
            # Bu adımda LLM'den gerçek bir yama / refaktör istenir.
            await self._synthesize_and_apply_patch(opportunity)
            
        except Exception as e:
            _log.error(f"Evolution consideration failure: {e}")

    async def _synthesize_and_apply_patch(self, opportunity: Dict[str, Any]):
        target_file = opportunity.get("target_file")
        if not target_file: return
        
        _log.info(f"Evrim Yaması Sentezleniyor: {target_file}")
        
        # Dosya içeriğini oku (Sembolik denetim için)
        import os
        if not os.path.exists(target_file):
            _log.warning(f"Evrim hedefi dosya bulunamadı: {target_file}")
            return

        with open(target_file, "r", encoding="utf-8") as f:
            current_code = f.read()

        patch_prompt = f"""
        HEDEF DOSYA: {target_file}
        MEVCUT KOD:
        ```python
        {current_code}
        ```
        
        GEREKÇE: {opportunity.get('reasoning')}
        ÖNERİLEN MANTIK: {opportunity.get('proposed_logic')}
        
        Lütfen bu dosyadaki hatalı kısmı düzelten veya iyileştiren YENİ KODU üret.
        Sadece tam dosya içeriğini veya net bir replacement bloğunu Python olarak ver.
        """
        
        try:
            resp = await self.model_orch.complete_task(
                agent_role="backend_dev",
                prompt=patch_prompt,
                system_prompt="Sen bir AGI Yazılım Mühendisisin. Kendi kodunu düzelten güvenli yamalar yazarsın."
            )
            
            # 3. GÜVENLİK DENETİMİ (Audit Gate) - Phase 23 Final
            from core.agi.schemas import ImprovementOpportunity
            opp_obj = ImprovementOpportunity(
                opportunity_id=opportunity.get("opportunity_id", "evolve_1"),
                title=opportunity.get("title", "Evolution"),
                score=0.8
            )
            
            is_safe = await self.audit.verify_evolution_patch(opp_obj, resp.content, target_file)
            
            if is_safe:
                _log.info(f"AUDIT ONAYI ALINDI. Evrim yaması uygulanıyor: {target_file}")
                # BURADA GERÇEK DOSYA YAZIMI YAPILIR (Dikkat: Hard Evolution)
                # with open(target_file, "w", encoding="utf-8") as f:
                #     f.write(resp.content)
                # _log.info("SİSTEM EVRİM GEÇİRDİ. (Autonomous Patch Applied)")
            else:
                _log.warning(f"AUDIT REDDİ. Evrim yaması iptal edildi.")
                
        except Exception as e:
            _log.error(f"Patch synthesis/apply failure: {e}")

# Singleton Instance
evolutionary_executor = EvolutionaryExecutor()
