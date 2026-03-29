import asyncio
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from core.improvement_v1.observer import ImprovementObserver, ImprovementOpportunity
from core.self_updater import SelfUpdater
from core.events import event_bus
from observability.logging import get_logger

logger = get_logger("self_improvement")

class SelfImprovementCoordinator:
    """
    Sistemin kendi kendini iyileştirme döngüsünü yöneten ana orkestratör (Faz 12).
    Döngü: Gözle (Observe) -> Önceliklendir -> Onay Al -> Uygula (Apply) -> Doğrula
    """
    
    def __init__(self, self_updater: SelfUpdater, observer: ImprovementObserver):
        self.updater = self_updater
        self.observer = observer
        self._is_running = False
        self._loop_task: Optional[asyncio.Task] = None

    async def start(self):
        if self._is_running:
            return
        self._is_running = True
        self._loop_task = asyncio.create_task(self._improvement_loop())
        logger.info("Self-Improvement Coordinator başlatıldı.")

    async def stop(self):
        self._is_running = False
        if self._loop_task:
            self._loop_task.cancel()
            try:
                await self._loop_task
            except (asyncio.CancelledError, Exception):
                pass
            self._loop_task = None
        logger.info("Self-Improvement Coordinator durduruldu.")

    async def _improvement_loop(self):
        """Periyodik tarama ve otomatik iyileştirme loop'u."""
        while self._is_running:
            try:
                # 1. Gözlem (Scan)
                opportunities = await self.observer.scan()
                if opportunities:
                    await self._process_opportunities(opportunities)
            except Exception as e:
                logger.error(f"Improvement loop hatası: {e}")
            
            await asyncio.sleep(3600) # Her saat başı tara

    async def _process_opportunities(self, opportunities: List[ImprovementOpportunity]):
        """Bulunan fırsatları sırayla işle."""
        # En yüksek önceliklileri seç
        sorted_ops = sorted(opportunities, key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(x.severity, 4))
        
        for op in sorted_ops:
            if not self._is_running: break
            
            # Risk değerlendirmesi
            requires_approval = self._check_risk(op)
            
            if requires_approval:
                await self._request_approval(op)
                continue
            
            # Otomatik iyileştirme (Düşük/Orta risk ise doğrudan)
            await self.apply_improvement(op)

    def _check_risk(self, op: ImprovementOpportunity) -> bool:
        """İyileştirmenin manuel onay gerektirip gerektirmediğini kontrol et."""
        # 1. Kritik/Yüksek severity her zaman onay ister
        if op.severity in ("critical", "high"):
            return True
        
        # 2. Hassas dosyalar onay ister
        for f in op.affected_files:
            if any(risk in f for risk in self.updater.HIGH_RISK_PATHS):
                return True
        
        return False

    async def _request_approval(self, op: ImprovementOpportunity):
        """Onay kapısına talep gönder."""
        await event_bus.emit(
            "improvement.pending_approval",
            opportunity_id=op.id,
            description=op.description,
            severity=op.severity,
            affected_files=op.affected_files,
            message=f"Kendi kendine iyileştirme onayı bekleniyor: {op.description}"
        )

    async def apply_improvement(self, op: ImprovementOpportunity) -> str:
        """Bir iyileştirme fırsatını uygula."""
        results = []
        for file_path in op.affected_files:
            try:
                out = await self.updater.modify_system_file(
                    target_file_path=file_path,
                    instruction=f"IMPROVEMENT REQUEST: {op.description}. Evidence: {op.evidence}"
                )
                results.append(f"{file_path}: {out}")
            except Exception as e:
                results.append(f"{file_path}: FAILED ({e})")
        
        summary = "\n".join(results)
        await event_bus.emit(
            "improvement.applied",
            opportunity_id=op.id,
            status="success" if "Başarılı" in summary else "partial",
            summary=summary,
            message=f"İyileştirme uygulandı: {op.description}"
        )
        return summary
