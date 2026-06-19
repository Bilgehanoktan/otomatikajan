import os
import sys
import asyncio
from pathlib import Path

# ── Import Yolu Ayarı ──
ROOT_DIR = str(Path(__file__).resolve().parents[2])
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from services.orchestration.application.job_queue import JobQueue
from services.observability.logging import get_logger

logger = get_logger("worker")

async def main():
    logger.info("Sovereign AGI Worker Başlatılıyor...")
    
    # Job Queue'yu başlat (Arka plan görevleri ve watchdog'lar)
    queue = JobQueue()
    await queue.start()
    
    logger.info("Worker aktif. Görevler dinleniyor.")
    
    # Worker'ın açık kalması için sonsuz döngü
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Worker kapatılıyor...")
        await queue.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
