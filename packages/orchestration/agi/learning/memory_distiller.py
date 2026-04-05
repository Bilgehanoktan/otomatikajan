import asyncio
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from packages.observability.logging import get_logger
from packages.llm_gateway.model_orchestrator import ModelOrchestrator
from packages.persistence.repositories.repository import MemoryRepository
from packages.persistence.session import AsyncSessionLocal

_log = get_logger("memory_distiller")

class MemoryDistiller:
    """
    [FAZ 73] Otomatik Kural Damıtma (Automatic Rule Distillation).
    Hafızadaki tekrarlayan hata ve başarısızlık örüntülerini analiz eder
    ve bunları kalıcı sistem kurallarına (System Instincts) dönüştürür.
    """

    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()

    async def run_distillation_cycle(self):
        """
        Tüm sistemi tarar ve yeni kurallar damıtır.
        """
        _log.info("[DISTILLER] Otonom kural damıtma döngüsü başlatılıyor...")
        
        async with AsyncSessionLocal() as db:
            # 1. Tekrarlayan başarısızlık desenlerini bul (Son 48 saat)
            patterns = await MemoryRepository.find_recurring_failures(db, limit_hours=48, min_count=2)
            
            if not patterns:
                _log.info("[DISTILLER] Belirgin bir başarısızlık örüntüsü saptanmadı.")
                return

            for p in patterns:
                _log.info(f"[DISTILLER] Örüntü tespit edildi: {p['agent_id']} -> '{p['pattern']}' ({p['frequency']} kez)")
                
                # 2. Örüntüden Kural Damıt (Architect via LLM)
                rule = await self._distill_rule_from_pattern(p)
                
                if rule:
                    # 3. Kuralı Sisteme Uygula
                    await self._register_system_instinct(rule, p)

    async def _distill_rule_from_pattern(self, pattern: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Başarısızlık örüntüsünü analiz eder ve bir mimari kural üretir.
        """
        prompt = f"""
        # AGI SİSTEM KURALI DAMITMA (PHASE 73)
        
        Sistemde tekrarlayan bir başarısızlık örüntüsü tespit edildi. 
        Bu hatanın bir daha yaşanmaması için kalıcı bir "Sistem İçgüdüsü" (System Instinct) üret.
        
        ÖRÜNTÜ:
        - Sorumlu Ajan: {pattern['agent_id']}
        - Hata Deseni: {pattern['pattern']}...
        - Tekrar Sayısı: {pattern['frequency']}
        
        GÖREV:
        1. Bu hatanın kök nedenini (root cause) tahmin et.
        2. Ajanın bir sonraki sefer bu hatayı yapmasını engelleyecek KESİN bir kural yaz.
        3. Kuralı "Her zaman X yap" veya "Asla Y yapma" şeklinde formüle et.
        
        Yanıtı JSON formatında ver:
        {{
            "rule_title": "Kural Başlığı",
            "root_cause": "Muhtemel neden",
            "instinct": "Kalıcı sistem içgüdüsü / kural metni",
            "severity": "high|medium|low"
        }}
        """
        
        try:
            response = await self.model_orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt="Sen Sovereign AGI'nin Baş Mimarısın. Hatalardan kalıcı dersler çıkarıp sistem anayasasını güncellersin."
            )
            
            if response and response.content:
                # JSON parse et
                match = __import__("re").search(r'\{.*\}', response.content, __import__("re").DOTALL)
                if match:
                    return json.loads(match.group())
        except Exception as e:
            _log.error(f"[DISTILLER] Kural damıtma LLM hatası: {e}")
        return None

    async def _register_system_instinct(self, rule: Dict[str, Any], source_pattern: Dict[str, Any]):
        """
        Üretilen kuralı sisteme kalıcı olarak kaydeder.
        """
        title = rule.get("rule_title", "Yeni Sistem Kuralı")
        instinct = rule.get("instinct", "")
        
        _log.warning(f"[DISTILLER-RULE] YENİ SİSTEM İÇGÜDÜSÜ DAMITILDI: {title}")
        _log.info(f"İçerik: {instinct}")

        # 1. Domain Event olarak kaydet (Audit Trail)
        from packages.persistence.repositories.repository import EventLogRepository
        async with AsyncSessionLocal() as db:
            await EventLogRepository.write(
                db=db,
                event_type="rule_distillation",
                agent_id="memory_distiller",
                severity=rule.get("severity", "medium"),
                message=f"Yeni kural damıtıldı: {title}",
                payload={
                    "rule": rule,
                    "source": source_pattern
                }
            )
            await db.commit()

        # 2. Kalıcı Hafıza (Wisdom) olarak kaydet
        from packages.orchestration.agi.cognitive.synaptic_cortex import synaptic_cortex
        async with AsyncSessionLocal() as db:
            await synaptic_cortex.save(
                db=db,
                agent_id="memory_distiller",
                body=f"SİSTEM KURALI ({title}): {instinct}",
                category="system_instinct",
                importance=0.9,
                tags=["distilled_rule", source_pattern['agent_id']]
            )
            await db.commit()

        # Phase 73: Bu noktada kural artık 'search_synergetic' tarafından 
        # otomatik olarak bulunup ilgili ajanlara enjekte edilecektir.

# Singleton
memory_distiller = MemoryDistiller()
