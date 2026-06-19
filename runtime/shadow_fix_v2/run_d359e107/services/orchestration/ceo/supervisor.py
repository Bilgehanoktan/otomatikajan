import asyncio
import json
import time
from datetime import datetime, timedelta, timezone

from libs.config import (
    CEO_ALERT_COOLDOWN_S,
    CEO_QUERY_BATCH_SIZE,
    CEO_SUPERVISOR_INTERVAL_S,
    TELEGRAM_BATCH_SLEEP_MS,
    TELEGRAM_BURST_LIMIT,
)
try:
    from libs.db.repositories.repository import ProjectRepository
except ImportError:
    pass  # lazy — gerçek kullanımda method içinde import edilir
try:
    from libs.db.session import session_scope
except ImportError:
    pass  # lazy — gerçek kullanımda method içinde import edilir
if TYPE_CHECKING:
    from services.repair.domain.agent_state import AgentSnapshot
    from libs.db.models.core_models import SubTask
    from services.orchestration.substrate.foundational_engine import FoundationalEngine as Orchestrator
from libs.llm.model_orchestrator import ModelOrchestrator
from services.observability.logging import get_logger
from services.governance.quality.prompt_guard import enforce_output_contract

logger = get_logger("ceo_supervisor")


class AutonomousCEO:
    def __init__(self, model_orch: ModelOrchestrator, telegram_notifier=None):
        self.model_orch = model_orch
        self.telegram = telegram_notifier

        self.daily_budget_limit = 5.0
        self.manifesto_path = "workspace/company_manifesto.md"

        self.last_rd_check = datetime.now(timezone.utc) - timedelta(hours=1)
        self.last_strategy_update = datetime.now(timezone.utc) - timedelta(hours=24)
        self.last_performance_review = datetime.now(timezone.utc) - timedelta(hours=12)

        # Yeni periyodik görev sayaçları
        self.last_manifesto_review = datetime.now(timezone.utc) - timedelta(hours=24)
        self.last_resource_check = datetime.now(timezone.utc) - timedelta(hours=1)
        self.last_budget_check = datetime.now(timezone.utc) - timedelta(hours=1)

        self.supervisor_interval_s = CEO_SUPERVISOR_INTERVAL_S
        self.alert_cooldown_s = CEO_ALERT_COOLDOWN_S
        self.query_batch_size = CEO_QUERY_BATCH_SIZE
        self.telegram_burst_limit = TELEGRAM_BURST_LIMIT
        self.telegram_batch_sleep_ms = TELEGRAM_BATCH_SLEEP_MS

        self._last_watch_ts = 0.0
        self._alert_cache: dict[str, float] = {}
        self._telegram_queue: list[str] = []

        # Opsiyonel yöneticiler; inject edilmezse güvenli şekilde skip edilecek
        self.resource_manager = None
        self.budget_manager = None

        self.system_prompt = """
Sen bu otonom yazılım şirketinin vizyoner CEO'susun.
Tıkanmış projeler için sadece doğrudan, 1-2 cümlelik kesin eylem kararları ver.
"""

    def _should_skip_cycle(self) -> bool:
        now = time.monotonic()
        if now - self._last_watch_ts < self.supervisor_interval_s:
            return True
        self._last_watch_ts = now
        return False

    def _dedupe_key(self, project_id: str, action: str) -> str:
        return f"{project_id}:{action}"

    def _can_alert(self, project_id: str, action: str) -> bool:
        now = time.time()
        key = self._dedupe_key(project_id, action)
        last = self._alert_cache.get(key, 0.0)
        if now - last < self.alert_cooldown_s:
            return False
        self._alert_cache[key] = now
        return True

    async def _queue_telegram_alert(self, message: str):
        if not self.telegram:
            return
        self._telegram_queue.append(message)

    async def _flush_telegram_alerts(self):
        if not self.telegram or not self._telegram_queue:
            return

        batch = self._telegram_queue[:]
        self._telegram_queue.clear()

        for idx in range(0, len(batch), self.telegram_burst_limit):
            chunk = batch[idx : idx + self.telegram_burst_limit]
            for msg in chunk:
                try:
                    await self.telegram.send_message(msg)
                except Exception as exc:
                    logger.warning(f"Telegram notify failed: {exc}")

            await asyncio.sleep(self.telegram_batch_sleep_ms / 1000)

    def _parse_json_robust(self, text: str):
        """Markdown kod bloklarından JSON'u temizleyen ve parse eden sağlam fonksiyon."""
        try:
            clean_text = enforce_output_contract(text, must_be_json=True)
            return json.loads(clean_text)
        except Exception as e:
            logger.error(f"❌ CEO JSON Parsing Hatası: {e} | Ham Metin: {text[:200]}")
            return None

    async def _review_company_manifesto(self):
        """Periodically review and update the company manifesto based on market changes."""
        now = datetime.now(timezone.utc)
        if (now - self.last_manifesto_review).total_seconds() > 86400:  # 24 hours
            logger.info("📜 CEO: Şirket manifestosu gözden geçiriliyor...")
            # Placeholder for actual manifesto review logic
            self.last_manifesto_review = now
            logger.info("📜 CEO: Manifesto gözden geçirme tamamlandı.")

    async def _allocate_resources(self):
        """Periodically allocate resources based on project priorities and needs."""
        now = datetime.now(timezone.utc)
        if (now - self.last_resource_check).total_seconds() <= 3600:
            return

        if self.resource_manager is None:
            logger.info("⚙️ CEO: resource_manager tanımlı değil, kaynak tahsisi atlandı.")
            self.last_resource_check = now
            return

        logger.info("⚙️ CEO: Kaynak tahsisi gözden geçiriliyor...")
        await self.resource_manager.reallocate_resources()
        self.last_resource_check = now
        logger.info("⚙️ CEO: Kaynak tahsisi tamamlandı.")

    async def _monitor_budget(self):
        """Periodically monitor the overall company budget and project budgets."""
        now = datetime.now(timezone.utc)
        if (now - self.last_budget_check).total_seconds() <= 3600:
            return

        logger.info("💰 CEO: Bütçe durumu izleniyor...")
        
        try:
            from libs.db.session import session_scope
            from libs.db.repositories.repository import CostRepository
            from libs.config import MONTHLY_BUDGET
            async with session_scope() as db:
                if hasattr(CostRepository, 'total_cost'):
                    total_spent = await CostRepository.total_cost(db)
                    if total_spent >= MONTHLY_BUDGET:
                        logger.warning(f"🚨 CEO Alarmı: Şirket aylık bütçesi doldu! (${total_spent} / ${MONTHLY_BUDGET})")
                        await self._queue_telegram_alert(f"🚨 Şirket Aylık Bütçe Sınırı Aşıldı: ${total_spent}")
                else:
                    raise RuntimeError("CostRepository.total_cost metodu bulunamadı!")
        except Exception as e:
            logger.error(f"❌ CEO Bütçe Kontrol Hatası: {e}")
            raise RuntimeError("CRITICAL: Bütçe tabloları veya bağlantısı koptu. Çalışma durduruluyor!") from e

        self.last_budget_check = now
        logger.info("💰 CEO: Bütçe izleme tamamlandı.")

    async def watch_and_govern(self):
        from services.orchestration.system_control import system_control

        if system_control.is_paused():
            return

        if self._should_skip_cycle():
            return

        logger.info("👔 CEO Stratejik Denetim Başlatıyor...")
        now = datetime.now(timezone.utc)

        try:
            await self._review_company_manifesto()
            await self._allocate_resources()
            await self._monitor_budget()

            async with session_scope() as db:
                from sqlalchemy import select
                from libs.db.models import Project, ProjectStatus

                result = await db.execute(
                    select(Project)
                    .where(Project.status.in_([
                        ProjectStatus.PENDING.value, 
                        ProjectStatus.QUEUED.value, 
                        ProjectStatus.RUNNING.value, 
                        ProjectStatus.PENDING_APPROVAL.value, 
                        ProjectStatus.ERROR.value
                    ]))
                    .limit(self.query_batch_size)
                )
                all_active = result.scalars().all()
                logger.info(f"👔 CEO Denetimi: {len(all_active)} aktif proje taranıyor...")

                # priority_level -> priority (Enum to Int mapping)
                p_map = {"critical": 10, "high": 8, "medium": 5, "low": 3}
                high_priority_exists = any(p_map.get(str(p.priority).lower(), 5) >= 9 for p in all_active)

                for proj in all_active:
                    # Faz 12.1 Refactor: Modellere göre öznitelik isimlerini güncelle
                    proj_time = getattr(proj, "updated_at", proj.created_at) or now
                    if proj_time.tzinfo is None:
                        proj_time = proj_time.replace(tzinfo=timezone.utc)
                    time_in_status = (now - proj_time).total_seconds()

                    stuck_reason = None
                    action = "watching"

                    # total_spent -> total_cost
                    spent = getattr(proj, "total_cost", 0.0)
                    limit = getattr(proj, "budget_limit", 1.0)
                    if spent >= limit:
                        if proj.status != ProjectStatus.PAUSED.value:
                            await self._apply_action(proj, "pause", db, "Proje bütçesi tükendi.")
                        continue

                    # priority_level -> priority (Enum to Int)
                    # TaskPriority: "critical" | "high" | "medium" | "low"
                    p_map = {"critical": 10, "high": 8, "medium": 5, "low": 3}
                    p_level = p_map.get(str(proj.priority).lower(), 5)
                    
                    if high_priority_exists and p_level < 4 and proj.status == ProjectStatus.RUNNING.value:
                        creation_time = proj.created_at or now
                        if creation_time.tzinfo is None:
                            creation_time = creation_time.replace(tzinfo=timezone.utc)
                        time_since_creation = (now - creation_time).total_seconds()

                        if time_since_creation < 3600:
                            if proj.status != ProjectStatus.PAUSED.value:
                                await self._apply_action(
                                    proj,
                                    "pause",
                                    db,
                                    "Yüksek öncelikli görevlere kaynak ayrıldı.",
                                )
                            continue

                    if proj.status in [ProjectStatus.PENDING.value, ProjectStatus.QUEUED.value] and time_in_status > 300:
                        stuck_reason = "Queue_Stuck: İşçi görevi henüz almadı (5 dk+)."
                        action = "requeue"
                    elif proj.status == ProjectStatus.RUNNING.value and time_in_status > 600:
                        stuck_reason = "Execution_Stuck: Ajanlar 10 dakikadır ilerlemiyor."
                        action = "escalate"
                    elif proj.status == ProjectStatus.PENDING_APPROVAL.value and time_in_status > 1800:
                        stuck_reason = "Waiting_Human: 30 dakikadır insan onayı yok."
                        action = "notify_human"
                    elif proj.status == ProjectStatus.ERROR.value and getattr(proj, "retry_count", 0) < 3:
                        stuck_reason = f"Task_Failed: Hata -> {str(proj.error_detail)[:100]}"
                        action = "retry"

                    if stuck_reason and proj.ceo_status != action and self._can_alert(str(proj.id), action):
                        logger.warning(f"🚨 CEO Alarmı: {proj.title} -> {stuck_reason}")

                        prompt = (
                            f"Proje: {proj.title}\n"
                            f"Durum: {proj.status}\n"
                            f"Sebep: {stuck_reason}\n"
                            f"Önerilen: {action}"
                        )

                        ceo_comment = await self.model_orch.complete(
                            messages=[
                                {"role": "system", "content": self.system_prompt},
                                {"role": "user", "content": prompt},
                            ],
                            preferred_agent="architect",
                        )

                        await ProjectRepository.update_fields(
                            db,
                            proj.id,
                            ceo_status=action,
                            stuck_reason=stuck_reason,
                            next_action=ceo_comment[:250],
                            last_supervised_at=now,
                        )

                        await self._apply_action(proj, action, db)
                        await self._queue_telegram_alert(
                            f"🚨 CEO Alarmı\nProje: {proj.title}\nAksiyon: {action}\nSebep: {stuck_reason}"
                        )

            await self._flush_telegram_alerts()

        except Exception as e:
            logger.error(f"❌ CEO Denetim Hatası: {e}")

        if (now - self.last_performance_review).total_seconds() > 43200:  # 12 saat
            try:
                from services.orchestration.employee_evolution import PerformanceReviewer

                reviewer = PerformanceReviewer(self.model_orch)
                await reviewer.evaluate_and_evolve()
                self.last_performance_review = now
            except Exception as e:
                logger.error(f"❌ CEO Evrim Tetikleme Hatası: {e}")

    async def _apply_action(self, proj, action, db, internal_reason=None):
        """CEO kararlarını veritabanına ve sisteme uygular."""
        from libs.db.models import TaskLog, ProjectStatus

        msg = internal_reason or f"CEO Action: {action}"
        logger.info(f"⚡ Uygulanan CEO Kararı: {proj.id} -> {action} ({msg})")

        new_log = TaskLog(
            project_id=proj.id,
            level="warning" if action in ["pause", "escalate"] else "info",
            event="ceo_intervention",
            message=msg,
            agent_id="CEO",
        )
        db.add(new_log)

        if action == "pause":
            await ProjectRepository.update_fields(db, proj.id, is_paused=True, status=ProjectStatus.PAUSED.value)

        elif action == "retry":
            from workers.workflow_worker.tasks.celery_app import celery_app

            new_count = getattr(proj, "retry_count", 0) + 1
            kwargs = {}
            if hasattr(proj, "workflow_template"):
                kwargs["workflow_template"] = proj.workflow_template
                kwargs["quality_profile"] = proj.quality_profile
                kwargs["acceptance_criteria"] = proj.acceptance_criteria
                kwargs["execution_context"] = proj.execution_context

            celery_task = celery_app.send_task(
                "run_project_task",
                args=[str(proj.id), proj.title, proj.description],
                kwargs=kwargs
            )
            await ProjectRepository.update_fields(
                db,
                proj.id,
                status=ProjectStatus.QUEUED.value,
                job_id=celery_task.id,
                retry_count=new_count,
            )

        elif action == "requeue":
            from workers.workflow_worker.tasks.celery_app import celery_app
            
            kwargs = {}
            if hasattr(proj, "workflow_template"):
                kwargs["workflow_template"] = proj.workflow_template
                kwargs["quality_profile"] = proj.quality_profile
                kwargs["acceptance_criteria"] = proj.acceptance_criteria
                kwargs["execution_context"] = proj.execution_context

            celery_task = celery_app.send_task(
                "run_project_task",
                args=[str(proj.id), proj.title, proj.description],
                kwargs=kwargs
            )
            await ProjectRepository.update_fields(
                db,
                proj.id,
                status=ProjectStatus.QUEUED.value,
                job_id=celery_task.id,
            )
            logger.info(f"✅ Görev yeniden kuyruğa eklendi: {proj.title} (Yeni Job ID: {celery_task.id})")

        elif action == "notify_human" and self.telegram:
            await self._queue_telegram_alert(
                f"🚨 *CEO ONAY BEKLİYOR*\nProje: {proj.title}\n30 dakikadır tepki verilmedi."
            )

    async def initiate_autonomous_rd(self):
        """
        CEO'nun periyodik Ar-Ge (Yeni özellik önerisi) süreci.
        Brittle split('```') yerine _parse_json_robust kullanılır.
        """
        if (datetime.now(timezone.utc) - self.last_rd_check).total_seconds() < 3600:
            return

        logger.info("🧪 CEO Ar-Ge Çalışması Başlatıyor...")
        self.last_rd_check = datetime.now(timezone.utc)

        prompt = "Şirketin geleceği için 3 yeni otonom Ar-Ge projesi öner. JSON formatında dön."
        resp = await self.model_orch.complete(
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt},
            ],
            preferred_agent="architect",
        )

        data = self._parse_json_robust(resp)
        if data:
            logger.info(f"✅ Ar-Ge Önerileri Alındı: {len(data)} adet.")
            # Burada projeler DB'ye kaydedilebilir veya duyurulabilir.
