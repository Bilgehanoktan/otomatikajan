import os
import json
import difflib
from typing import List, Dict, Any, Optional
from packages.observability.logging import get_logger
from packages.llm_gateway.model_orchestrator import model_orchestrator
from packages.persistence.session import session_scope
from sqlalchemy import select
from packages.persistence.models import ImprovementOpportunity, CEOSuggestedTask
from packages.orchestration.agi.operational.neural_tool_weaver import neural_tool_weaver
from packages.orchestration.agi.cognitive.causal_engine import causal_engine

_log = get_logger("agi_evolutionary_architect")

class EvolutionaryArchitect:
    """
    Operational Core (Katman 32): Evolutionary Architect (Evrimsel Mimar).
    Sistemin kendi kodundaki hataları veya iyileştirme alanlarını saptayıp
    bunlara yönelik yama (patch) önerileri üretmesini ve dinamik yetenek sentezlemesini sağlar.
    """
    
    ALLOWED_DIRECTORIES = ["core/agi/", "scripts/", "tasks/", "db/repository.py"]

    async def propose_evolution(self):
        """
        Açık iyileştirme fırsatlarını tarar ve kod yaması önerir.
        """
        _log.info("Evrimsel Mimari (Evolutionary Architecture) analizi başlatılıyor...")
        
        async with session_scope() as db:
            # 1. Açık fırsatları bul (Özellikle rüya/bilinçaltı/gecikmeli zihin kaynaklı olanlar)
            result = await db.execute(
                select(ImprovementOpportunity)
                .where(ImprovementOpportunity.status == "open")
                .order_by(ImprovementOpportunity.priority_score.desc())
                .limit(3)
            )
            opportunities = result.scalars().all()
            
            if not opportunities:
                _log.info("Evrimsel Mimar: İşlenecek açık iyileştirme fırsatı bulunamadı.")
                return

            for opp in opportunities:
                # KRİTİK SEÇİM: Yama mı yoksa Yeni Araç mı? [Katman 32]
                if "tool" in opp.category.lower() or "new capability" in opp.description.lower():
                    # A. YETENEK SENTEZİ (Skill Synthesis)
                    _log.info(f"Evrimsel Mimar: '{opp.title}' için YETENEK SENTEZİ (Tool Weaving) başlatılıyor.")
                    res = await neural_tool_weaver.weave_capability(opp.description)
                    if res.get("status") == "success":
                        opp.status = "synthesized"
                        _log.info(f"Evrimsel Mimar: Yeni araç başarıyla sentezlendi: {res.get('tool_name')}")
                        continue

                # B. KOD YAMASI (Patching)
                target_file = await self._detect_target_file(opp)
                if not target_file or not self._is_allowed(target_file):
                    _log.warning(f"Evrimsel Mimar: '{opp.title}' için hedef dosya saptanamadı veya izin verilmedi.")
                    continue
                
                # 3. Yama Sentezi
                try:
                    with open(target_file, "r", encoding="utf-8") as f:
                        original_code = f.read()
                    
                    patch_suggestion = await self._synthesize_patch(opp, target_file, original_code)
                    
                    if patch_suggestion:
                        # 4. Güvenlik Denetimi (Audit Gate) [Katman 31]
                        from packages.orchestration.agi.security.audit_gate import AuditGate
                        audit_gate = AuditGate(model_orchestrator)
                        is_safe = await audit_gate.verify_evolution_patch(opp, patch_suggestion, target_file)
                        
                        if not is_safe:
                            _log.warning(f"Evrimsel Mimar: '{target_file}' yaması güvenlik denetiminden geçemedi.")
                            continue

                        # 5. CEO Önerisi Olarak Kaydet (Approval Gate için)
                        suggestion = CEOSuggestedTask(
                            opportunity_id=opp.id,
                            title=f"[EVOLUTION] {opp.title}",
                            description=f"File: {target_file}\n\nREASON: {opp.description}\n\nSUGGESTED PATCH:\n{patch_suggestion}",
                            priority=opp.severity,
                            status="suggested",
                            reasoning_summary="Gecikmeli zihin analizi sonucunda saptanan kod hatası/iyileştirmesi için otomatik yama üretildi ve Güvenlik Denetminden geçti."
                        )
                        db.add(suggestion)
                        # Fırsatı 'analiz edildi' durumuna çekebiliriz veya açık bırakabiliriz
                        opp.status = "analyzed"
                        _log.info(f"Evrimsel Mimar: '{target_file}' için evrimsel yama önerildi.")
                except Exception as e:
                    _log.error(f"Evrimsel Mimar yama sentezi hatası: {e}")

    async def _detect_target_file(self, opp: ImprovementOpportunity) -> Optional[str]:
        """Causal Engine ve RepoGraph ile akıllı dosya tespiti."""
        _log.debug(f"Evrimsel Mimar: '{opp.title}' için hedef dosya saptanıyor...")
        
        # 1. Eğer evidence içinde spesifik bir dosya varsa (Observer'dan gelen)
        if opp.evidence and "file" in opp.evidence:
            return opp.evidence["file"]

        # 2. Nedensellik Analizi (Causal Engine)
        # Not: EpisodeRecord gerektirdiği için her fırsatta (Opportunity) Episode verisi olmayabilir.
        # Bu durumda başlık/açıklamadan regex ile fallback yapılır.
        
        text = f"{opp.title} {opp.description} {opp.evidence_detail}"
        # core/agi/... scripts/... gibi desenleri ara
        match = re.search(r'(core/agi/[a-zA-Z0-9_\-/]+\.py|scripts/[a-zA-Z0-9_\-]+\.py|db/repository\.py)', text)
        if match:
            target = match.group(1)
            _log.info(f"Evrimsel Mimar: Dosya tespiti (Regex): {target}")
            return target
            
        return None

    def _is_allowed(self, path: str) -> bool:
        return any(path.startswith(prefix) for prefix in self.ALLOWED_DIRECTORIES)

    async def _synthesize_patch(self, opp: ImprovementOpportunity, filename: str, code: str) -> Optional[str]:
        prompt = f"""
        Aşağıdaki iyileştirme fırsatını temel alarak '{filename}' dosyasındaki kodu revize et.
        
        İYLEŞTİRME FIRSATI:
        {opp.title}: {opp.description}
        
        MEVCUT KOD ({filename}):
        ```python
        {code}
        ```
        
        Lütfen SADECE değiştirilmesi gereken kısmın YENİ HALİNİ bir Python fonksiyonu veya bloğu olarak döndür. 
        Tüm dosyayı döndürme. Sadece spesifik değişikliği göster.
        """
        
        response = await model_orchestrator.complete_task(
            agent_role="senior_developer",
            prompt=prompt,
            system_prompt="Sen bir AGI Evrimsel Mimarı (Evolutionary Architect). Kendi kodundaki hataları en güvenli ve temiz şekilde düzeltirsin."
        )
        return response.content

    def _parse_diff(self, original: str, proposed: str) -> str:
        # Gelecekte gerçek difflib kullanımı için
        return proposed

import re

# Singleton
evolutionary_architect = EvolutionaryArchitect()
