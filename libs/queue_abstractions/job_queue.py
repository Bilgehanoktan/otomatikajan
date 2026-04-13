"""
Async Job Queue — Faz 2
• API istek döner -> arka planda çalışır (non-blocking)
• Job ID ile durum takibi
• Redis varsa Celery, yoksa in-process asyncio worker
• Dead-letter queue: kalıcı başarısızlıklar ayrı depoya
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Awaitable, Callable, Optional
from services.observability.logging import get_logger  # type: ignore

_log = get_logger("libs.queue_abstractions.job_queue")

class JobStatus(str, Enum):
    PENDING  = "pending"
    RUNNING  = "running"
    COMPLETED= "completed"
    ERROR    = "error"
    RETRYING = "retrying"
    PAUSED   = "paused"
    DEAD     = "dead"      # kalıcı başarısızlık -> dead-letter


@dataclass
class Job:
    id:          str
    type:        str
    payload:     dict
    status:      JobStatus      = JobStatus.PENDING
    result:      Any            = None
    error:       str            = ""
    attempts:    int            = 0
    max_attempts:int            = 3
    created_at:  str            = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_at:  str            = ""
    completed_at:str            = ""


@dataclass(frozen=True)
class QueueCapabilities:
    backend_name: str = "unknown"
    supports_registration: bool = False
    supports_listing: bool = False
    supports_dead_letters: bool = False
    supports_cancel: bool = False
    supports_pause: bool = False
    supports_resume: bool = False
    listing_scope: str = "unknown"  # global | process_local | none

class BaseQueueCapabilities:
    capabilities = QueueCapabilities()


# ════════════════════════════════════════════════════════
# In-Process Job Queue (Redis/Celery yoksa)
# ════════════════════════════════════════════════════════
class JobQueue(BaseQueueCapabilities):
    """
    asyncio tabanlı in-process kuyruk.
    Tek process'te yeterli; çok worker gerekirse Celery'ye geçilir.
    """

    def __init__(self, concurrency: int = 4, max_retry_wait: float = 30.0):
        self.backend_name  = "inprocess"
        self.capabilities = QueueCapabilities(
            backend_name="inprocess",
            supports_registration=True,
            supports_listing=True,
            supports_dead_letters=True,
            supports_cancel=True,
            supports_pause=True,
            supports_resume=True,
            listing_scope="global",
        )
        self._queue:       asyncio.Queue      = asyncio.Queue()
        self._jobs:        dict[str, Job]     = {}
        self._dead_letter: list[Job]          = []
        self._handlers:    dict[str, Callable] = {}
        self._semaphore:   asyncio.Semaphore  = asyncio.Semaphore(concurrency)
        self._max_retry_wait = max_retry_wait
        self._running      = False
        self._workers:     list[asyncio.Task] = []
        
        # Capability Flags (Sync with dataclass for backward compat)
        self.supports_registration = self.capabilities.supports_registration
        self.supports_listing      = self.capabilities.supports_listing
        self.supports_dead_letters = self.capabilities.supports_dead_letters
        self.supports_cancel       = self.capabilities.supports_cancel
        self.supports_pause        = self.capabilities.supports_pause
        self.supports_resume       = self.capabilities.supports_resume

    def register(self, job_type: str, handler: Callable[..., Awaitable]):
        """İş tipine işleyici bağla."""
        self._handlers[job_type] = handler

    async def enqueue(self, job_type: str, **payload) -> Job:
        """Kuyruğa iş ekle, Job nesnesi döndür."""
        job = Job(
            id=payload.get("job_id") or str(uuid.uuid4())[:12],  # type: ignore
            type=job_type,
            payload=payload,
        )
        self._jobs[job.id] = job
        _log.info(f"Job enqueued: {job.id} (type: {job_type})")
        
        # Eğer PENDING ise kuyruğa ekle (Hydration sırasında RUNNING olanlar kuyruğa tekrar girmesin, sadece listede dursunlar)
        if job.status == JobStatus.PENDING:
            await self._queue.put(job)
        return job

    async def hydrate_from_db(self):
        """DB'deki açık projeleri (Task) belleğe yükler (Faz 12.1 Persistence Fix)."""
        _log.info("Hydrating standard tasks from DB...")
        try:
            from db.session import AsyncSessionLocal
            from db.repository import ProjectRepository
            
            async with AsyncSessionLocal() as db:
                # Sadece aktif (tamamlanmamış) işleri çekelim
                active_statuses = ["PENDING", "RUNNING", "QUEUED", "RETRYING", "PAUSED"]
                projects = await ProjectRepository.list_recent(db, limit=100)
                
                count = 0
                for p in projects:
                    # status enum veya string gelebilir, normalize edelim
                    p_status = str(p.status.value if hasattr(p.status, "value") else p.status).upper()
                    
                    if p_status in active_statuses:
                        job_id = p.job_id or str(p.id)
                        if job_id not in self._jobs:
                            job = Job(
                                id=job_id,
                                type="run_project",
                                payload={"db_project_id": str(p.id), "title": p.title},
                                status=self._map_db_status_to_job(p_status),
                                created_at=p.created_at.isoformat() if p.created_at else ""
                            )
                            self._jobs[job.id] = job
                            if job.status == JobStatus.PENDING:
                                await self._queue.put(job)
                            count += 1
                
                _log.info(f"Successfully hydrated {count} tasks into JobQueue.")
                return count
        except Exception as e:
            _log.error(f"Failed to hydrate tasks: {e}", exc_info=True)
            return 0

    def _map_db_status_to_job(self, db_status: str) -> JobStatus:
        s = str(db_status).upper()
        mapping = {
            "PENDING": JobStatus.PENDING,
            "QUEUED": JobStatus.PENDING,
            "RUNNING": JobStatus.RUNNING,
            "RETRYING": JobStatus.RETRYING,
            "PAUSED": JobStatus.PAUSED,
        }
        return mapping.get(s, JobStatus.PENDING)

    def get_job(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

        return list(tuple(self._jobs.values())[-limit:])  # type: ignore

    @property
    def dead_letters(self) -> list[Job]:
        return self._dead_letter.copy()

    # ── Worker Döngüsü ────────────────────────────────────
    async def start(self, num_workers: int = 2):
        self._running = True
        for i in range(num_workers):
            task = asyncio.create_task(self._worker(f"worker-{i}"))
            self._workers.append(task)
        # Zombi Avcısı'nı başlat
        self._workers.append(asyncio.create_task(self._zombie_sweeper()))

    async def stop(self):
        self._running = False
        for w in self._workers:
            w.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()

    async def _worker(self, name: str):
        while self._running:
            try:
                job = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

            _log.info(f"Worker {name} picked up job: {job.id}")
            async with self._semaphore:
                try:
                    await self._execute(job)
                except Exception as e:
                    _log.error(f"Worker {name} DIED processing job {job.id}: {e}", exc_info=True)
                    job.status = JobStatus.ERROR
                    job.error = f"Beklenmeyen Worker Hatası: {str(e)}"
            self._queue.task_done()

    async def _zombie_sweeper(self):
        """Arka planda çalışarak kilitlenmiş (zombi) işleri periyodik olarak temizler."""
        while self._running:
            await asyncio.sleep(60)  # Her dakikada bir kontrol et
            now = datetime.now(timezone.utc)
            for job in list(self._jobs.values()):
                if job.status == JobStatus.RUNNING and job.started_at:
                    try:
                        started = datetime.fromisoformat(job.started_at)
                        if (now - started).total_seconds() > 1800:  # 30 Dakika sınırı
                            _log.error(f"🧟 Zombi iş tespit edildi (30dk+ RUNNING): {job.id}")
                            self.request_cancel(job.id)
                    except Exception:
                        pass

    # ── Cancel token: job_id -> asyncio.Event ─────────────
    _cancel_tokens: dict[str, asyncio.Event] = {}

    def request_cancel(self, job_id: str) -> bool:
        """İptal sinyali gönder. Job çalışıyorsa bir sonraki kontrol noktasında durur."""
        token = self._cancel_tokens.get(job_id)
        if token:
            token.set()
            return True
        job = self._jobs.get(job_id)
        if job and job.status in (JobStatus.PENDING, JobStatus.RETRYING):
            job.status = JobStatus.ERROR
            job.error  = "Kullanıcı tarafından iptal edildi"
            job.completed_at = datetime.now(timezone.utc).isoformat()
            return True
        return False

    def pause_job(self, job_id: str) -> bool:
        """İşi duraklat."""
        job = self._jobs.get(job_id)
        if job and job.status == JobStatus.RUNNING:
            job.status = JobStatus.PAUSED
            _log.info(f"Job paused: {job_id}")
            return True
        return False

    def resume_job(self, job_id: str) -> bool:
        """İşi devam ettir."""
        job = self._jobs.get(job_id)
        if job and job.status == JobStatus.PAUSED:
            job.status = JobStatus.RUNNING
            _log.info(f"Job resumed: {job_id}")
            return True
        return False

    async def _execute(self, job: Job):
        handler = self._handlers.get(job.type)
        if not handler:
            job.status = JobStatus.DEAD
            job.error  = f"Bilinmeyen iş tipi: {job.type}"
            self._dead_letter.append(job)
            return

        # İptal edilmiş olabilir (kuyruktayken işaretlendiyse)
        if job.status == JobStatus.ERROR and "iptal" in job.error.lower():
            return

        cancel_event = asyncio.Event()
        self._cancel_tokens[job.id] = cancel_event

        try:
            while job.attempts < job.max_attempts:
                # Her deneme öncesi iptal kontrolü
                if cancel_event.is_set():
                    job.status = JobStatus.ERROR
                    job.error  = "Kullanıcı tarafından iptal edildi"
                    job.completed_at = datetime.now(timezone.utc).isoformat()
                    return

                # Duraklatma kontrolü
                while job.status == JobStatus.PAUSED:
                    if cancel_event.is_set():
                        job.status = JobStatus.ERROR
                        job.error  = "Kullanıcı tarafından iptal edildi (duraklatılmışken)"
                        job.completed_at = datetime.now(timezone.utc).isoformat()
                        return
                    await asyncio.sleep(1.0)

                job.attempts   += 1
                job.status      = JobStatus.RUNNING
                job.started_at  = datetime.now(timezone.utc).isoformat()

                try:
                    # İptal sinyali veya gerçek handler — hangisi önce biterse
                    handler_task = asyncio.ensure_future(handler(**job.payload))
                    cancel_task  = asyncio.ensure_future(cancel_event.wait())

                    done, pending = await asyncio.wait(
                        {handler_task, cancel_task},
                        timeout=600,  # 10 dk hard limit
                        return_when=asyncio.FIRST_COMPLETED,
                    )

                    # Temizlik
                    t: asyncio.Task
                    for t in pending:  # type: ignore
                        t.cancel()
                        try:
                            await t
                        except (asyncio.CancelledError, Exception):
                            pass

                    if cancel_event.is_set():
                        job.status       = JobStatus.ERROR
                        job.error        = "Kullanıcı tarafından iptal edildi"
                        job.completed_at = datetime.now(timezone.utc).isoformat()
                        return

                    if not done:
                        raise asyncio.TimeoutError()

                    if handler_task in done:
                        exc = handler_task.exception()
                        if exc:
                            raise exc
                        job.result       = handler_task.result()
                        job.status       = JobStatus.COMPLETED
                        job.completed_at = datetime.now(timezone.utc).isoformat()
                        return

                except asyncio.TimeoutError:
                    job.error  = "Zaman aşımı (600s)"
                    job.status = JobStatus.RETRYING
                except asyncio.CancelledError:
                    job.status = JobStatus.ERROR
                    job.error  = "İptal edildi"
                    return
                except Exception as e:
                    job.error  = f"{type(e).__name__}: {e}"
                    job.status = JobStatus.RETRYING
                    _log.warning(f"Job {job.id} deneme {job.attempts}/{job.max_attempts} başarısız: {job.error}")

                if job.attempts < job.max_attempts:
                    wait = min(2 ** job.attempts, self._max_retry_wait)
                    await asyncio.sleep(wait)

            # Tüm denemeler tükendi -> dead-letter
            job.status       = JobStatus.DEAD
            job.completed_at = datetime.now(timezone.utc).isoformat()
            self._dead_letter.append(job)
            _log.error(f"❌ Job {job.id} KALICI BAŞARISIZLIK (Dead Letter): {job.error}")

        finally:
            self._cancel_tokens.pop(job.id, None)

    # ── İstatistik ────────────────────────────────────────
    def stats(self) -> dict:
        jobs = list(self._jobs.values())
        by_status = {s.value: 0 for s in JobStatus}  # type: ignore
        for j in jobs:
            by_status[j.status.value] += 1  # type: ignore
        return {
            "queue_size":  self._queue.qsize(),
            "total":       len(jobs),
            "total_jobs":  len(jobs),    # geriye dönük uyumluluk
            "running":     by_status.get("running", 0),
            "pending":     by_status.get("pending", 0),
            "completed":   by_status.get("completed", 0),
            "error":       by_status.get("error", 0) + by_status.get("dead", 0),
            "by_status":   by_status,
            "dead_letters":len(self._dead_letter),
            "workers":     len(self._workers),
        }

    def cancel_running(self, job_id: str) -> bool:
        """request_cancel ile aynı; daha açık isim."""
        return self.request_cancel(job_id)



# ════════════════════════════════════════════════════════
# Celery Bağdaştırıcısı (Redis varsa tercih edilir)
# ════════════════════════════════════════════════════════
class CeleryJobQueue(BaseQueueCapabilities):
    """
    ⚠️ DEPRECATED — Canonical queue = JobQueue (in-process, asyncio tabanlı).
    Bu sınıf Redis/Celery varsa kullanılabilir ama main.py tarafından
    yüklenmez. İleride kaldırılacaktır.

    Aynı interface — Celery'ye delege eder.
    Kullanım: job_queue = CeleryJobQueue() if redis_available else JobQueue()
    """

    def __init__(self):
        self.backend_name = "celery"
        self.capabilities = QueueCapabilities(
            backend_name="celery",
            supports_registration=False,
            supports_listing=True,
            supports_dead_letters=False,
            supports_cancel=False,
            supports_pause=False,
            supports_resume=False,
            listing_scope="process_local",
        )
        try:
            from tasks.celery_app import celery_app  # type: ignore
            from tasks.project_tasks import run_project_task  # type: ignore
            self._celery = celery_app
            self._run_task = run_project_task
            self._available = True
            self._jobs: dict[str, Job] = {} # CeleryJobQueue needs to track jobs too
        except ImportError:
            self._available = False
            
        # Capability Flags (Sync with dataclass)
        self.supports_registration = self.capabilities.supports_registration
        self.supports_listing      = self.capabilities.supports_listing
        self.supports_dead_letters = self.capabilities.supports_dead_letters
        self.supports_cancel       = self.capabilities.supports_cancel
        self.supports_pause        = self.capabilities.supports_pause
        self.supports_resume       = self.capabilities.supports_resume

    async def enqueue(self, job_type: str, **payload) -> Job:
        """Celery ile işi kuyruğa ekler."""
        job_id = payload.pop("job_id", str(uuid.uuid4())[:12])  # type: ignore
        job = Job(id=job_id, type=job_type, payload=payload, status=JobStatus.PENDING)
        self._jobs[job_id] = job

        if not self._available:
            _log.warning(f"⚠️ Celery kullanılamıyor, iş {job_id} PENDING kaldı.")
            return job

        # Görev adı eşleştirme (Faz 12 Dinamik Mapping + DeerFlow Rolleri)
        task_map = {
            "run_project":       "tasks.project_tasks.run_project_task",
            "send_webhook":      "tasks.project_tasks.send_webhook_task",
            "cleanup":           "tasks.project_tasks.cleanup_memories",
            "self_update":       "tasks.project_tasks.run_self_update_task",
            "deerflow_run":      "tasks.deerflow_tasks.run_deerflow_streaming_task",
            "deerflow_plan":     "tasks.deerflow_tasks.run_deerflow_streaming_task",
            "deerflow_research": "tasks.deerflow_tasks.run_deerflow_streaming_task",
            "deerflow_review":   "tasks.deerflow_tasks.run_deerflow_streaming_task",
            "deerflow_recovery": "tasks.deerflow_tasks.run_deerflow_streaming_task",
        }

        # Kuyruk eşleştirme — DeerFlow türleri izole kuyruğa
        from config import QUEUE_DEFAULT, QUEUE_DEERFLOW  # type: ignore
        _DEERFLOW_JOB_TYPES = {"deerflow_run", "deerflow_plan", "deerflow_research", "deerflow_review", "deerflow_recovery"}
        
        task_name = task_map.get(job_type)
        if not task_name:
            _log.error(f"❌ Bilinmeyen görev tipi: {job_type}")
            job.status = JobStatus.ERROR
            job.error  = f"Bilinmeyen görev tipi: {job_type}"
            return job

        target_queue = QUEUE_DEERFLOW if job_type in _DEERFLOW_JOB_TYPES else QUEUE_DEFAULT

        # Metadata enjeksiyonu (Role propagation)
        task_kwargs = {**payload, "job_id": job_id}
        if job_type in _DEERFLOW_JOB_TYPES:
            task_kwargs["deerflow_role"] = job_type

        try:
            self._celery.send_task(
                task_name,
                kwargs=task_kwargs,
                task_id=job_id,
                queue=target_queue
            )
            # job.status = JobStatus.PENDING (default) - DO NOT set to RUNNING here!
            _log.info(f"📤 Celery'ye gönderildi: {task_name} | ID: {job_id}")
        except Exception as e:
            _log.error(f"❌ Celery send_task hatası: {e}")
            job.status = JobStatus.ERROR
            job.error = str(e)
            
        return job

    async def hydrate_from_db(self):
        """DB'deki açık projeleri belleğe yükler (Celery Sync Fix)."""
        _log.info("Hydrating standard tasks from DB for Celery backend...")
        try:
            from db.session import AsyncSessionLocal
            from db.repository import ProjectRepository
            
            async with AsyncSessionLocal() as db:
                active_statuses = ["PENDING", "RUNNING", "QUEUED", "RETRYING", "PAUSED"]
                projects = await ProjectRepository.list_recent(db, limit=100)
                
                count = 0
                for p in projects:
                    p_status = str(p.status.value if hasattr(p.status, "value") else p.status).upper()
                    if p_status in active_statuses:
                        job_id = p.job_id or str(p.id)
                        if job_id not in self._jobs:
                            job = Job(
                                id=job_id,
                                type="run_project",
                                payload={"db_project_id": str(p.id), "title": p.title},
                                status=JobStatus.PENDING 
                            )
                            self._jobs[job.id] = job
                            count += 1
                
                _log.info(f"Successfully hydrated {count} tasks into CeleryJobQueue cache.")
                return count
        except Exception as e:
            _log.error(f"Failed to hydrate Celery tasks: {e}")
            return 0

    def get_job(self, job_id: str) -> Job | None:
        """Celery'den güncel durumu sorgula, yerel metadata ile birleştir (Dürüstlük)."""
        if not self._available:
            return self._jobs.get(job_id)

        try:
            from celery.result import AsyncResult  # type: ignore
            res = AsyncResult(job_id, app=self._celery)
            
            # Bellekteki orijinal job'ı bul veya yeni taslak oluştur
            job = self._jobs.get(job_id)
            if not job:
                job = Job(id=job_id, type="unknown", payload={})
                self._jobs[job_id] = job

            # Celery state'ini dürüstçe yansıt
            job.status = _celery_state_to_job(res.state)
            if res.ready():
                job.result = res.result
                if res.failed():
                    job.error = str(res.result)
            
            return job
        except Exception as e:
            _log.debug(f"Celery status query error for {job_id}: {e}")
            return self._jobs.get(job_id)

    def stats(self) -> dict:
        """Celery durumlarını bellekteki işler üzerinden özetle."""
        jobs = self.list_jobs(100)
        by_status = {s.value: 0 for s in JobStatus}  # type: ignore
        for j in jobs:
            updated = self.get_job(j.id)
            if updated:
                by_status[updated.status.value] += 1  # type: ignore
        
        return {
            "backend":     "celery",
            "available":   self._available,
            "total":       len(self._jobs),
            "total_jobs":  len(self._jobs),
            "running":     by_status.get("running", 0),
            "pending":     by_status.get("pending", 0),
            "completed":   by_status.get("completed", 0),
            "error":       by_status.get("error", 0) + by_status.get("dead", 0),
            "by_status":   by_status,
        }

    def list_jobs(self, limit: int = 50) -> list[Job]:
        """Celery tabanlı işleri listele (sadece bu process tarafından bilinenler)."""
        return list(tuple(self._jobs.values())[-limit:])  # type: ignore

    @property
    def dead_letters(self) -> list[Job]:
        """Celery için dead-letter takibi in-memory (basit fallback)."""
        return [j for j in self._jobs.values() if j.status == JobStatus.DEAD]

    async def start(self, num_workers: int = 2):
        _log.info(f"CeleryJobQueue: Yerel worker başlatılmadı, harici Celery worker'ları kullanılıyor (num_workers={num_workers} atlandı).")

    async def stop(self):
        _log.info("CeleryJobQueue durduruluyor (bağlantı temizliği).")

    def register(self, job_type: str, handler: Any):
        _log.debug(f"CeleryJobQueue: {job_type} için handler kaydedildi (Celery tarafında karşılığı olmalı).")


def _celery_state_to_job(state: str) -> JobStatus:
    return {
        "PENDING":  JobStatus.PENDING,
        "STARTED":  JobStatus.RUNNING,
        "SUCCESS":  JobStatus.COMPLETED,
        "FAILURE":  JobStatus.ERROR,
        "RETRY":    JobStatus.RETRYING,
        "REVOKED":  JobStatus.DEAD,
    }.get(state, JobStatus.PENDING)


# ── Singleton ─────────────────────────────────────────────
from config import REDIS_URL, WORKER_CONCURRENCY, QUEUE_BACKEND  # type: ignore

def create_job_queue():
    backend = (QUEUE_BACKEND or "auto").lower()

    if backend == "celery":
        return CeleryJobQueue()

    if backend == "inprocess":
        return JobQueue(concurrency=WORKER_CONCURRENCY)

    # auto mode
    env_redis = os.getenv("REDIS_URL")
    if env_redis or REDIS_URL:
        return CeleryJobQueue()

    return JobQueue(concurrency=WORKER_CONCURRENCY)

job_queue = create_job_queue()
