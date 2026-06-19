"""
Resilience Agent — Phase 45 (Otonom Dayanıklılık ve Kurtarma)
─────────────────────────────────────────────────────────────
Sistem kesintiye uğradığında (crash/restart) INTERRUPTED durumuna 
düşen görevleri analiz eder ve güvenli olanları otonom olarak 
kaldığı yerden devam ettirir.
"""

import asyncio
from typing import List
from datetime import datetime, timezone

from services.observability.logging import get_logger
from libs.db.models import Project, ProjectStatus
from services.orchestration.agi.cognitive.sovereign_cortex import sovereign_cortex
from libs.db.session import AsyncSessionLocal

_log = get_logger("agi_resilience_agent")

class ResilienceAgent:
    def __init__(self):
        self._running = False
        self._task: asyncio.Task | None = None
        self._check_interval = 60  # 1 dakika

    async def start(self):
        if self._running: return
        self._running = True
        self._task = asyncio.create_task(self._recovery_loop())
        _log.info("Resilience Agent aktif. Kesintiye ugrayan gorevler izleniyor.")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try: await self._task
            except asyncio.CancelledError: pass
        _log.info("Resilience Agent durduruldu.")

    async def _recovery_loop(self):
        # İlk çalışma: Sistem açıldığında hemen kontrol et
        await asyncio.sleep(5)  # Sistemin tam oturması için kısa bekleme
        
        while self._running:
            try:
                await self.scan_and_recover()
            except Exception as e:
                _log.error(f"Resilience döngüsünde hata: {e}", exc_info=True)
            await asyncio.sleep(self._check_interval)

    async def scan_and_recover(self):
        """Kesintiye ugrayan projeleri tarar ve kurtarir."""
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as db:
            # INTERRUPTED durumundaki projeleri bul
            stmt = select(Project).where(Project.status == ProjectStatus.INTERRUPTED)
            res = await db.execute(stmt)
            interrupted_projects = res.scalars().all()
            
            if not interrupted_projects:
                return

            _log.info(f"Otonom kurtarma: {len(interrupted_projects)} adet kesintiye ugrayan gorev tespit edildi. Analiz ediliyor...")
            
            for project in interrupted_projects:
                # Risk Analizi
                is_recoverable = self._assess_recovery_risk(project)
                
                if is_recoverable:
                    _log.warning(f"Gorev otonom olarak kurtariliyor: {project.title} ({project.id})")
                    project.status = ProjectStatus.RESUMING
                    await db.commit()
                    
                    # Cortex üzerinden devam ettir (Arka planda)
                    asyncio.create_task(self._resume_project(project.id))
                else:
                    _log.error(f"Gorev kurtarma icin cok riskli bulundu: {project.title}")
                    project.status = ProjectStatus.ERROR
                    project.error_detail = "Kritik kesinti: Islem riskli oldugu icin otonom kurtarilamadi."
                    await db.commit()

    def _assess_recovery_risk(self, project: Project) -> bool:
        """Gorevin kurtarilma riskini analiz eder (False positive onlendi)."""
        import re
        description = (project.description or "").lower()
        title = project.title.lower()
        
        # Riskli kelimeler - Tam kelime eşleşmesi (Whole word)
        # 'sil' kelimesinin 'resilience' içinde geçmesini engellemek için regex kullanıyoruz.
        risk_patterns = [r"\bdelete\b", r"\bremove\b", r"\bwipe\b", r"\bformat\b", r"\bsil\b", r"\btemizle\b"]
        
        for pattern in risk_patterns:
            if re.search(pattern, description) or re.search(pattern, title):
                return False
            
        return True

    async def _resume_project(self, project_id: str):
        """Cortex üzerinden görevi resume et."""
        try:
            # sovereign_cortex'e resume_goal yeteneği ekledik
            if hasattr(sovereign_cortex, "resume_goal"):
                await sovereign_cortex.resume_goal(project_id)
            else:
                _log.error("Cortex 'resume_goal' yetenegine sahip degil. Klasik baslatma deneniyor.")
                # Fallback: Mevcut coordinate_goal'u project_id ile çağır
                from libs.db.session import AsyncSessionLocal
                async with AsyncSessionLocal() as db:
                    from libs.db.repositories.repository import ProjectRepository
                    p = await ProjectRepository.get(db, project_id)
                    if p:
                        await sovereign_cortex.coordinate_goal(
                            title=p.title,
                            description=p.description,
                            project_id=p.id,
                            execution_context=p.execution_context
                        )
        except Exception as e:
            _log.error(f"Proje resume hatası ({project_id}): {e}")

# Singleton
resilience_agent = ResilienceAgent()
