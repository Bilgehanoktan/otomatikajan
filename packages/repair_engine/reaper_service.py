"""
Reaper Service â€” Zombie Job Clean-up (Phase 6)
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
Sistem Ã¼zerinde asÄ±lÄ± kalan (zombi), zaman aÅŸÄ±mÄ±na uÄŸramÄ±ÅŸ veya 
kapanmamÄ±ÅŸ iÅŸleri (RepairJob) tespit eder ve temizler.
"""

import asyncio
import time
from datetime import datetime, timezone
from packages.observability.logging import get_logger

_log = get_logger("core.reaper")

class ReaperService:
    def __init__(self, check_interval_m: int = 15, timeout_hours: int = 1):
        self.check_interval = check_interval_m * 60
        self.timeout_hours = timeout_hours
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self):
        if self._running: return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        _log.info(f"Reaper Service baÅŸlatÄ±ldÄ±. (Interval: {self.check_interval}s, Timeout: {self.timeout_hours}h)")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try: await self._task
            except asyncio.CancelledError: pass
        _log.info("Reaper Service durduruldu.")

    async def _run_loop(self):
        while self._running:
            try:
                await self.reap()
            except Exception as e:
                _log.error(f"Reaper dÃ¶ngÃ¼sÃ¼nde hata: {e}", exc_info=True)
            await asyncio.sleep(self.check_interval)

    async def reap(self):
        """AsÄ±lÄ± kalan iÅŸleri DB Ã¼zerinden tespit et ve temizle."""
        from packages.persistence.session import AsyncSessionLocal, is_db_available
        if not await is_db_available():
            return

        from packages.persistence.repositories.repair_repository import RepairJobRepo
        from packages.repair_engine.application.orchestrator import get_repair_orchestrator

        orch = get_repair_orchestrator()
        
        async with AsyncSessionLocal() as db:
            # 1. Zombi iÅŸleri bul
            zombies = await RepairJobRepo.find_zombies(db, threshold_hours=self.timeout_hours)
            if not zombies:
                return

            _log.warning(f"ğŸ§Ÿ {len(zombies)} adet zombi iÅŸ tespit edildi. Temizleniyor...")
            
            job_ids = [z.job_id for z in zombies]
            
            # 2. Toplu olarak FAILED durumuna Ã§ek
            reason = f"Reaper: Job exceeded {self.timeout_hours}h limit and was marked as zombie."
            count = await RepairJobRepo.bulk_fail(db, job_ids, reason)
            
            await db.commit()
            _log.info(f"Reaper: {count} iÅŸ temizlendi.")

            # 3. Orchestrator cache'ini gÃ¼ncelle (varsa)
            for jid in job_ids:
                if jid in orch._jobs_cache:
                    job = orch._jobs_cache[jid]
                    job.status = job.status.__class__.FAILED_VALIDATION  # Fallback terminal state
                    job.error_detail = reason
                    # Cache'ten uÃ§urmak yerine terminale Ã§ekmek daha gÃ¼venli
                    
# Singleton
reaper = ReaperService(check_interval_m=30, timeout_hours=1)

