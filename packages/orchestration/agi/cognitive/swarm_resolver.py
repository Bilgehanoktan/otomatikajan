import asyncio
from typing import List, Dict, Any, Optional
from observability.logging import get_logger
from llm.model_orchestrator import ModelOrchestrator
from packages.orchestration.agi.schemas import ActionRecord, PlanStep

_log = get_logger("agi_swarm_resolver")

class SwarmResolver:
    """
    Sürü Zekası Çözümleyici (Swarm Resolver).
    Ajanlar arası işbirliği, akran denetimi (peer review) ve uzlaşı (consensus)
    süreçlerini yönetir.
    """
    
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()

    async def orchestrate_peer_review(self, 
                                     producer_id: str, 
                                     reviewer_id: str, 
                                     task_context: Dict[str, Any],
                                     produced_output: Any) -> Dict[str, Any]:
        """
        Bir ajanın çıktısını başka bir ajana denetletir ve gerekirse revize ettirir.
        """
        _log.info(f"[SWARM] Akran denetimi başlatıldı: {producer_id} -> {reviewer_id}")
        
        # --- Neuro-Symbolic Verification (Phase 26) ---
        from core.agi.cognitive.symbolic_prover import symbolic_prover
        from core.agi.security.symbolic_engine import symbolic_engine
        import tempfile
        import os

        # Kod bloğu ise sembolik kontrolden geçirt
        if isinstance(produced_output, str) and ("def " in produced_output or "class " in produced_output):
            _log.info(f"[SWARM] Nöro-Sembolik doğrulama başlatılıyor: {producer_id}")
            
            # 1. Sembolik İspat (Prover)
            proof = symbolic_prover.prove_proposal(produced_output)
            if not proof["is_proven"]:
                _log.warning(f"[SWARM] Sembolik İspat BAŞARISIZ: {proof['proof_summary']}")
                return await self._refined_by_symbolic(producer_id, produced_output, f"SEMANTİK İHLAL: {proof['violations']}")
            
            # 2. Sembolik Motor (Tool-based Scans)
            with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tmp:
                tmp.write(produced_output.encode())
                tmp_path = tmp.name
            
            try:
                safety_res = await symbolic_engine.run_safety_scans(tmp_path)
                if not safety_res["is_valid"]:
                    _log.warning("[SWARM] Sembolik Motor Denetimi BAŞARISIZ.")
                    return await self._refined_by_symbolic(producer_id, produced_output, f"GÜVENLİK/TİP HATASI: {safety_res}")
            finally:
                if os.path.exists(tmp_path): os.remove(tmp_path)

        # Standart Akran Denetimi (Neural)
        review_prompt = f"""
        Aşağıdaki görev bağlamında, {producer_id} tarafından üretilen çıktıyı incele.
        Hata, güvenlik açığı veya iyileştirme fırsatı varsa belirt.
        
        GÖREV: {task_context.get('objective', 'Bilinmiyor')}
        ÜRETİLEN ÇIKTI: {produced_output}
        
        Yanıtını formatla:
        STATUS: [APPROVED | REJECTED]
        FEEDBACK: [Detaylı geri bildirim]
        """
        
        review_res = await self.model_orch.complete_task(
            agent_role=reviewer_id,
            prompt=review_prompt,
            system_prompt="Sen bir Akran Denetçisisin (Peer Reviewer). Çıktıları titizlikle inceler ve eksikleri bulursun."
        )
        
        content = review_res.content
        is_approved = "STATUS: APPROVED" in content
        feedback = content.split("FEEDBACK:")[-1].strip() if "FEEDBACK:" in content else ""
        
        if is_approved:
            _log.info(f"[SWARM] {reviewer_id} çıktıyı ONAYLADI.")
            return {"status": "approved", "final_output": produced_output, "review": feedback}
        
        # 2. Revizyon (Refine)
        _log.warning(f"[SWARM] {reviewer_id} çıktıyı REDDETTİ. Revizyon başlatılıyor.")
        refine_prompt = f"""
        Ürettiğin önceki çıktı denetçi ({reviewer_id}) tarafından reddedildi.
        Geri bildirimi dikkate alarak çıktıyı güncelle.
        
        GERİ BİLDİRİM: {feedback}
        ÖNCEKİ ÇIKTI: {produced_output}
        """
        
        refine_res = await self.model_orch.complete_task(
            agent_role=producer_id,
            prompt=refine_prompt,
            system_prompt=f"Geri bildirimleri hızla uygulayan bir {producer_id} uzmanısın."
        )
        
        return {
            "status": "refined",
            "final_output": refine_res.content,
            "review": feedback,
            "revision_notes": "Geri bildirim uygulandı."
        }

    async def _refined_by_symbolic(self, producer_id: str, old_output: str, error_report: str) -> Dict[str, Any]:
        """Sembolik hata saptandığında otomatik revizyon tetikler."""
        _log.info(f"[SWARM] Sembolik revizyon döngüsü: {producer_id}")
        
        prompt = f"""
        Ürettiğin kod sembolik (symbolic) doğrulamayı GEÇEMEDİ. 
        Aşağıdaki resmi hataları düzeltmelisin.
        
        HATA RAPORU: {error_report}
        ÖNCEKİ KOD: {old_output}
        """
        
        res = await self.model_orch.complete_task(
            agent_role=producer_id,
            prompt=prompt,
            system_prompt=f"Sen bir {producer_id} uzmanısın. Sembolik (Formal) hatalara tolerans göstermez ve onları hızla fixlersin."
        )
        
        return {
            "status": "symbolically_refined",
            "final_output": res.content,
            "review": f"Symbolic Fix applied: {error_report}"
        }

    async def resolve_consensus(self, 
                                agent_a_out: str, 
                                agent_b_out: str, 
                                task_objective: str) -> str:
        """
        İki ajan farklı çözümler sunduğunda bir 'Lead' (Architect) ile uzlaşı sağlar.
        """
        _log.info("[SWARM] Uzlaşı (Consensus) süreci başlatıldı.")
        
        consensus_prompt = f"""
        İki uzman farklı çözümler/görüşler sundu. Bir 'Lead Architect' olarak en doğru yolu seç veya sentezle.
        
        GÖREV: {task_objective}
        GÖRÜŞ A: {agent_a_out}
        GÖRÜŞ B: {agent_b_out}
        
        Kararını gerekçesiyle birlikte ver.
        """
        
        res = await self.model_orch.complete_task(
            agent_role="architect",
            prompt=consensus_prompt,
            system_prompt="Sen bir Baş Mimarsın. Uzmanlar arasındaki anlaşmazlıkları çözer ve en teknik/güvenli yolu belirlersin."
        )
        
        return res.content

# Singleton
swarm_resolver = SwarmResolver()
