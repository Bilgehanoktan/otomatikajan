"""
Celery Görev Kuyruğu
• Redis broker + result backend
• Öncelikli kuyruklar: critical > default > background
• Görev yeniden deneme (retry) ile üstel bekleme
• Proje görevlerini arka planda çalıştırır
"""

import os
import sys
try:
    from celery import Celery
    from celery.utils.log import get_task_logger
except ImportError:
    raise ImportError(
        "celery paketi bulunamadı. Kurmak için: pip install celery[redis]\n"
        "Test ortamında çalıştırıyorsanız TEST_STUB_LEVEL=warn ile pytest çalıştırın."
    )

# ── Import Yolu Ayarı (ÇOK KRİTİK!) ──
from pathlib import Path
ROOT_DIR = str(Path(__file__).resolve().parents[3])
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

logger = get_task_logger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
QUEUE_BACKEND = os.getenv("QUEUE_BACKEND", "celery")
CELERY_ENABLED = os.getenv("CELERY_ENABLED", "true").lower() == "true"

broker_url = REDIS_URL
backend_url = REDIS_URL

if QUEUE_BACKEND == "inprocess" or not CELERY_ENABLED:
    broker_url = "memory://"
    backend_url = "cache+memory://"

celery_app = Celery(
    "ai_company",
    broker=broker_url,
    backend=backend_url,
    include=[
        "workers.workflow_worker.tasks.project_tasks",
        "workers.workflow_worker.tasks.deerflow_tasks",
        "workers.workflow_worker.tasks.mesh_tasks",
        "workers.workflow_worker.tasks.ui_repair_tasks",
    ],
)

celery_app.conf.update(
    # Serileştirme
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,

    # Kuyruk önceliği
    task_routes={
        "workers.workflow_worker.tasks.project_tasks.run_project_task":    {"queue": "default"},
        "workers.workflow_worker.tasks.project_tasks.heal_check_task":     {"queue": "critical"},
        "workers.workflow_worker.tasks.project_tasks.send_webhook_task":   {"queue": "background"},
        "workers.workflow_worker.tasks.project_tasks.cleanup_memories":    {"queue": "background"},
        "workers.workflow_worker.tasks.deerflow_tasks.run_deerflow_task": {"queue": "deerflow"},
        "workers.workflow_worker.tasks.deerflow_tasks.run_deerflow_streaming_task": {"queue": "deerflow"},
    },

# Yeniden deneme
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
)

# ── Periyodik Görevler (Beat Schedule) ──────────────────
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    # Mesh Pulse (Heartbeat) - Her 10 saniyede bir
    "mesh-pulse-10s": {
        "task": "workers.workflow_worker.tasks.mesh_tasks.mesh_pulse_task",
        "schedule": 10.0,
        "options": {"queue": "critical"},
    },
    # Her gün gece 03:00'te görsel denetim yap
    "visual-audit-daily": {
        "task": "workers.workflow_worker.tasks.project_tasks.run_visual_audit_task",
        "schedule": crontab(hour=3, minute=0),
    },
    # Her 6 saatte bir pazar istihbaratı tara
    "market-intel-6h": {
        "task": "workers.workflow_worker.tasks.project_tasks.run_market_intelligence_task",
        "schedule": crontab(hour="*/6", minute=30),
    },
    # Her Pazar gece 04:00'te bellek temizliği
    "cleanup-memories-weekly": {
        "task": "workers.workflow_worker.tasks.project_tasks.cleanup_memories",
        "schedule": crontab(day_of_week=0, hour=4, minute=0),
    },
    # UI Smoke Monitor (Her 5 dakikada bir)
    "ui-smoke-monitor-5m": {
        "task": "workers.workflow_worker.tasks.ui_repair_tasks.ui_smoke_monitor_task",
        "schedule": 300.0,
        "options": {"queue": "background"},
    },
}




# ── LOGLAMA ENTEGRASYONU (Faz 12 Fix) ───────────────────
from services.observability.logging import configure_logging, get_logger

@celery_app.on_after_finalize.connect
def setup_direct_logging(sender, instance=None, **kwargs):
    """Worker başladığında loglamayı yapılandır."""
    configure_logging()
    get_logger("tasks", force_db=True)
    get_logger("workers.workflow_worker.tasks.project_tasks", force_db=True)
    get_logger("workers.workflow_worker.tasks.deerflow_tasks", force_db=True)


try:
    from celery.signals import setup_logging, after_setup_logger

    @setup_logging.connect
    def on_setup_logging(loglevel, logfile, format, customize, **kwargs):
        """Celery'nin kendi loglamasını bizimkine bağla."""
        configure_logging()
        return False # Celery'nin varsayılan handler'larını ezme (ama biz ekledik)

    @after_setup_logger.connect
    def on_after_setup_logger(logger, *args, **kwargs):
        """Her logger oluştuğunda bizim handler'larımızı ekle."""
        from services.observability.logging import DBLogHandler
        # DB handler yoksa ekle (güvence)
        if not any(isinstance(h, DBLogHandler) for h in logger.handlers):
            logger.addHandler(DBLogHandler())

except ImportError:
    pass


# Sonuç saklama
celery_app.conf.result_expires = 604800  # 7 gün (Faz 12 Persistence Fix)
