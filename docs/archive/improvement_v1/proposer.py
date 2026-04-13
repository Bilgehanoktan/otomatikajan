"""
Patch Proposer — Faz 9 Güncellemesi
• Gerçek LLM çağrısı (model_orchestrator üzerinden)
• Whitelist ile güvenli dosya hedefleme
• unified diff formatında yama üretimi
"""

import os
import uuid
import logging
from typing import Optional
from .models import ImprovementOpportunity, PatchProposal

logger = logging.getLogger(__name__)


class PatchProposer:
    """Belirlenen fırsatlar için LLM ile yama önerisi üretir."""

    # Otomatik yamalanabilecek güvenli dosyalar
    SAFE_TARGETS = [
        "heal/recovery_strategies.py",
        "config.py",
        "core/prompts.py",
    ]

    def __init__(self, project_root: str):
        self.project_root = project_root

    async def propose(self, opportunity: ImprovementOpportunity) -> Optional[PatchProposal]:
        """
        1. Etkilenen dosyaları oku.
        2. LLM'e problem bağlamı, dosya içeriği ve metrikleri ver.
        3. Unified diff al.
        4. Güvenlik kontrolü yap.
        """
        target_file = self._find_safe_target(opportunity.affected_files)
        if not target_file:
            logger.info("Bu fırsat için güvenli hedef dosya bulunamadı.")
            return None

        file_path = os.path.join(self.project_root, target_file)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                current_code = f.read()
        except Exception as e:
            logger.error(f"Hedef dosya okunamadı {target_file}: {e}")
            return None

        diff = await self._call_llm(opportunity, target_file, current_code)
        if not diff:
            logger.warning("LLM diff üretemedi veya boş döndü.")
            return None

        return PatchProposal(
            id=str(uuid.uuid4()),
            opportunity_id=opportunity.id,
            target_file=target_file,
            diff=diff,
            explanation=f"Otonom düzeltme — {opportunity.source_metric}: {opportunity.description}",
            risk_score=0.4,
        )

    def _find_safe_target(self, affected_files: list[str]) -> Optional[str]:
        """Güvenli hedef dosyayı seç."""
        for target in affected_files:
            full_path = target if os.path.isabs(target) else os.path.join(self.project_root, target)
            rel_path  = os.path.relpath(full_path, self.project_root)
            if ".." in rel_path or rel_path.startswith("."):
                continue
            if rel_path in self.SAFE_TARGETS:
                return rel_path
        return None

    async def _call_llm(
        self,
        opportunity: ImprovementOpportunity,
        target_file: str,
        current_code: str,
    ) -> str:
        """
        Gerçek LLM çağrısı — model_orchestrator üzerinden.
        Başarısız olursa boş string döner.
        """
        prompt = (
            f"PROBLEM: {opportunity.description}\n"
            f"METRİKLER: {opportunity.evidence}\n"
            f"DOSYA: {target_file}\n"
            f"İÇERİK:\n---\n{current_code[:3000]}\n---\n\n"
            "GÖREV: Yukarıdaki problemi gideren minimal bir UNIFIED DIFF üret.\n"
            "Sadece unified diff formatında yama döndür, açıklama ekleme."
        )
        try:
            from hub_cortex.llm_gateway.model_orchestrator import ModelOrchestrator
            orch = ModelOrchestrator()
            result = await orch.complete(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
            )
            # Diff içeriğini temizle
            diff = result.strip()
            if not diff.startswith("---"):
                # LLM bazen ek açıklama eklemiş olabilir — diff bloğunu çıkar
                if "---" in diff:
                    diff = diff[diff.index("---"):]
            return diff
        except Exception as e:
            logger.error(f"LLM diff üretimi başarısız: {e}")
            return ""
