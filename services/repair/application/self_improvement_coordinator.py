import asyncio
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from services.repair.improvement.observer import ImprovementObserver, ImprovementOpportunity
from services.orchestration.application.self_updater import SelfUpdater
from services.orchestration.domain.events import event_bus
from services.observability.logging import get_logger

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
        logger.info("Self-Improvement Coordinator baslatildi.")

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
            
            await asyncio.sleep(900) # Her 15 dakikada bir tara (Stabilizasyon Modu)

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
        """
        Stage 1: Analyze opportunity, generate patch, verify in shadow, and save to DB.
        Does NOT touch the real disk.
        """
        from libs.db.models.core_models import SystemImprovement
        from services.orchestration.application.shadow_runner import ShadowRunner
        
        affected_files = getattr(op, "affected_files", []) or []
        if not affected_files:
            return "No affected files."

        results = []
        for file_path in affected_files:
            try:
                # 1. Shadow Workspace'de düzeltme üret ve test et
                instruction = f"FIX RECURRING ERROR: {op.description}. Evidence: {op.evidence_detail}"
                
                # LLM'den düzeltme iste
                suggested_code = await self.updater.propose_fix(file_path, instruction)
                
                # Shadow Runner ile izole ortamda doğrula
                shadow = ShadowRunner(self.updater.project_root)
                validation = await asyncio.to_thread(shadow.validate_candidate, file_path, suggested_code)
                
                is_valid = validation.get("syntax_ok", False) and (validation.get("pytest_ok") is not False)
                test_report = f"Syntax: {validation.get('syntax_ok')}, Pytest: {validation.get('pytest_ok')}"
                
                # 2. Veritabanına 'Pending' olarak kaydet
                from libs.db.session import AsyncSessionLocal
                async with AsyncSessionLocal() as db:
                    improvement = SystemImprovement(
                        id=uuid.uuid4(),
                        opportunity_id=op.id,
                        target_file=file_path,
                        instruction=instruction,
                        proposed_patch=suggested_code,
                        status="pending",
                        test_results={
                            "valid": is_valid,
                            "report": test_report,
                            "shadow_verified_at": datetime.now(timezone.utc).isoformat()
                        }
                    )
                    db.add(improvement)
                    await db.commit()

                results.append(f"{file_path}: PROPOSED (Shadow Verified: {is_valid})")
            except Exception as e:
                logger.error(f"Improvement proposal failed for {file_path}: {e}")
                results.append(f"{file_path}: FAILED ({e})")
        
        return "\n".join(results)

    async def run_effector(self):
        """
        Stage 2: Effector Phase.
        Scan for APPROVED improvements and apply them to the real disk.
        """
        from libs.db.session import AsyncSessionLocal
        from libs.db.models.core_models import SystemImprovement
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            res = await db.execute(
                select(SystemImprovement).where(SystemImprovement.status == "approved")
            )
            approved_list = res.scalars().all()

            if not approved_list:
                return

            print(f"[SelfImprovement] Found {len(approved_list)} approved improvements. Applying...")

            for imp in approved_list:
                try:
                    # Physically apply the patch
                    target_path = Path(self.updater.project_root) / imp.target_file
                    with open(target_path, "w", encoding="utf-8") as f:
                        f.write(imp.proposed_patch)
                    
                    imp.status = "applied"
                    imp.applied_at = datetime.now(timezone.utc)
                    logger.info(f"SUCCESSFULLY APPLIED PATCH to {imp.target_file}")
                except Exception as e:
                    logger.error(f"Failed to apply patch {imp.id}: {e}")
                    imp.status = "failed"
                
            await db.commit()
