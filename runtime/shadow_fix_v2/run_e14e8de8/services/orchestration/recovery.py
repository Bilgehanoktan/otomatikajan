import asyncio
import logging
from sqlalchemy import select
from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import Project, ProjectStatus
from libs.workflow.runner import WorkflowRunner

logger = logging.getLogger(__name__)

class RecoveryService:
    """
    Sovereign AGI Recovery Service (Faz 13.04)
    System startup veya periyodik check sırasında yarım kalmış (RUNNING)
    workflow'ları tespit eder ve onları Durable Engine üzerinden kaldığı yerden devam ettirir.
    """
    
    def __init__(self):
        self.runner = WorkflowRunner()

    async def scan_and_recover(self):
        """Yarım kalmış workflow'ları bul ve canlandır."""
        logger.info("Scanning for interrupted workflows to recover...")
        
        async with AsyncSessionLocal() as session:
            # Sadece RUNNING durumunda olan (aktif olarak bir worker tarafından tutulması gereken ama worker çökmüş olabilir)
            # ve son güncellenmesi üzerinden belli bir süre geçmiş olanları da seçebiliriz.
            # Şimdilik direkt RUNNING olanları alıyoruz.
            res = await session.execute(
                select(Project).where(Project.status == ProjectStatus.RUNNING)
            )
            projects = res.scalars().all()
            
            if not projects:
                logger.info("No interrupted workflows found.")
                return

            logger.info(f"Found {len(projects)} workflows to recover.")
            
            for project in projects:
                logger.info(f"Recovering project: {project.id} ({project.name})")
                # Runner.run_project asenkron çalışır ve içindeki engine 
                # history'ye bakarak zaten tamamlanmış adımları atlar.
                # Arka planda başlatalım (background task)
                asyncio.create_task(self.runner.run_project(str(project.id)))

    async def run_forever(self, interval_seconds: int = 300):
        """Periyodik olarak kontrol et."""
        while True:
            try:
                await self.scan_and_recover()
            except Exception as e:
                logger.error(f"Recovery loop error: {e}")
            await asyncio.sleep(interval_seconds)

if __name__ == "__main__":
    # Tek seferlik recovery testi
    logging.basicConfig(level=logging.INFO)
    service = RecoveryService()
    asyncio.run(service.scan_and_recover())
