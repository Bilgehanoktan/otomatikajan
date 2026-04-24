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
    Sistemin kendi kendini iyileÅŸtirme dÃ¶ngÃ¼sÃ¼nÃ¼ yÃ¶neten ana orkestratÃ¶r (Faz 12).
    DÃ¶ngÃ¼: GÃ¶zle (Observe) -> Ã–nceliklendir -> Onay Al -> Uygula (Apply) -> DoÄŸrula
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
        logger.info("Self-Improvement Coordinator baÅŸlatÄ±ldÄ±.")

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
        """Periyodik tarama ve otomatik iyileÅŸtirme loop'u."""
        while self._is_running:
            try:
                # 1. GÃ¶zlem (Scan)
                opportunities = await self.observer.scan()
                if opportunities:
                    await self._process_opportunities(opportunities)
            except Exception as e:
                logger.error(f"Improvement loop hatasÄ±: {e}")
            
            await asyncio.sleep(3600) # Her saat baÅŸÄ± tara

    async def _process_opportunities(self, opportunities: List[ImprovementOpportunity]):
        """Bulunan fÄ±rsatlarÄ± sÄ±rayla iÅŸle."""
        # En yÃ¼ksek Ã¶nceliklileri seÃ§
        sorted_ops = sorted(opportunities, key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(x.severity, 4))
        
        for op in sorted_ops:
            if not self._is_running: break
            
            # Risk deÄŸerlendirmesi
            requires_approval = self._check_risk(op)
            
            if requires_approval:
                await self._request_approval(op)
                continue
            
            # Otomatik iyileÅŸtirme (DÃ¼ÅŸÃ¼k/Orta risk ise doÄŸrudan)
            await self.apply_improvement(op)

    def _check_risk(self, op: ImprovementOpportunity) -> bool:
        """Ä°yileÅŸtirmenin manuel onay gerektirip gerektirmediÄŸini kontrol et."""
        # 1. Kritik/YÃ¼ksek severity her zaman onay ister
        if op.severity in ("critical", "high"):
            return True
        
        # 2. Hassas dosyalar onay ister
        for f in op.affected_files:
            if any(risk in f for risk in self.updater.HIGH_RISK_PATHS):
                return True
        
        return False

    async def _request_approval(self, op: ImprovementOpportunity):
        """Onay kapÄ±sÄ±na talep gÃ¶nder."""
        await event_bus.emit(
            "improvement.pending_approval",
            opportunity_id=op.id,
            description=op.description,
            severity=op.severity,
            affected_files=op.affected_files,
            message=f"Kendi kendine iyileÅŸtirme onayÄ± bekleniyor: {op.description}"
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
                # 1. Shadow Workspace'de dÃ¼zeltme Ã¼ret ve test et
                instruction = f"FIX RECURRING ERROR: {op.description}. Evidence: {op.evidence_detail}"
                
                # Shadow Runner ile izole ortamda deneme yap
                shadow = ShadowRunner(self.updater.project_root)
                shadow_path = await shadow.create_shadow_copy(file_path)
                
                # LLM'den dÃ¼zeltme iste (shadow dosya Ã¼zerinde)
                suggested_code = await self.updater.propose_fix(file_path, instruction)
                
                # Shadow dosyayÄ± gÃ¼ncelle
                with open(shadow_path, "w", encoding="utf-8") as f:
                    f.write(suggested_code)
                
                # DoÄŸrulama (Syntax + Tests)
                is_valid, test_report = await shadow.verify_shadow(shadow_path)
                
                # 2. VeritabanÄ±na 'Pending' olarak kaydet
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

