"""
Telegram Bot — Faz 4
• /start /help /status /tasks /task /newtask /agents /logs /errors /queue /metrics
• Kullanıcı yetkilendirme (is_authorized DB kontrolü)
• Komut geçmişi loglama (TelegramCommandLog)
• Sistem bildirimleri (hata, tamamlama, kritik alarm)
• Görevler "telegram" source olarak işaretlenir
• python-telegram-bot kütüphanesi kullanılır

Kurulum: pip install python-telegram-bot>=20.0
Env:      TELEGRAM_BOT_TOKEN=... TELEGRAM_ALLOWED_IDS=123456,789012
"""

import asyncio
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from packages.packages.observability.logging import get_logger
from core.task_routing import task_router
from packages.orchestration.application.job_queue import job_queue
from core.events import event_bus

logger = get_logger("telegram.bot")

# ── Env yapılandırma ────────────────────────────────────────
BOT_TOKEN     = os.getenv("TELEGRAM_BOT_TOKEN", "")
# Virgülle ayrılmış Telegram ID whitelist (DB kontrolü olmadan hızlı erişim)
ALLOWED_IDS   = set(
    filter(None, os.getenv("TELEGRAM_ALLOWED_IDS", "").split(","))
)
ADMIN_IDS     = set(
    filter(None, os.getenv("TELEGRAM_ADMIN_IDS", "").split(","))
)

# ── Lazy imports (telegram paket opsiyonel) ─────────────────
def _tg_available() -> bool:
    try:
        import telegram  # noqa
        return True
    except ImportError:
        return False


# ══════════════════════════════════════════════════════════
# Yetkilendirme
# ══════════════════════════════════════════════════════════
async def _is_authorized(telegram_id: str) -> bool:
    """Önce env whitelist, sonra DB kontrolü."""
    if telegram_id in ALLOWED_IDS:
        return True
    try:
        from packages.persistence.session import AsyncSessionLocal
        from packages.persistence.repository import TelegramRepository
        async with AsyncSessionLocal() as db:
            return await TelegramRepository.is_authorized(db, telegram_id)
    except Exception:
        return False


async def _is_admin(telegram_id: str) -> bool:
    if telegram_id in ADMIN_IDS:
        return True
    try:
        from packages.persistence.session import AsyncSessionLocal
        from packages.persistence.repository import TelegramRepository
        async with AsyncSessionLocal() as db:
            user = await TelegramRepository.get_user(db, telegram_id)
            return user is not None and user.is_admin
    except Exception:
        return False


async def _log_command(
    telegram_id: str,
    command: str,
    arguments: str,
    response: str,
    success: bool = True,
    project_id=None,
):
    try:
        from packages.persistence.session import AsyncSessionLocal
        from packages.persistence.repository import TelegramRepository
        async with AsyncSessionLocal() as db:
            await TelegramRepository.log_command(
                db, telegram_id, command, arguments,
                response=response[:2000], success=success, project_id=project_id,
            )
            await packages.persistence.commit()
    except Exception:
        pass


async def _upsert_user(telegram_id: str, username: str, full_name: str):
    try:
        from packages.persistence.session import AsyncSessionLocal
        from packages.persistence.repository import TelegramRepository
        async with AsyncSessionLocal() as db:
            await TelegramRepository.upsert_user(db, telegram_id, username, full_name)
            await packages.persistence.commit()
    except Exception:
        pass


# ══════════════════════════════════════════════════════════
# Komut İşleyicileri
# ══════════════════════════════════════════════════════════
class BotCommandHandler:
    """Her komut için handler metodu."""

    # ── /start ─────────────────────────────────────────────
    async def cmd_start(self, tid: str, args: str) -> str:
        auth = await _is_authorized(tid)
        if not auth:
            return (
                "👋 *Otonom Yazılım Şirketi Bot*\n\n"
                "Bu bot sadece yetkili kullanıcılara açıktır.\n"
                f"Erişim için yöneticiye Telegram ID'nizi (`{tid}`) bildirin.\n\n"
                "Eğer yetkiniz varsa /help ile başlayabilirsiniz."
            )
        return (
            "🏢 *Otonom Yazılım Geliştirme Şirketi*\n\n"
            "Merhaba! Sisteme bağlısınız.\n\n"
            "Kullanılabilir komutlar için /help yazın.\n"
            "Sistem durumu için /status yazın."
        )

    # ── /help ──────────────────────────────────────────────
    async def cmd_help(self, tid: str, args: str) -> str:
        is_admin = await _is_admin(tid)
        base = (
            "📋 *Komut Listesi*\n\n"
            "📊 *Durum ve İzleme*\n"
            "/status — Sistem genel durumu\n"
            "/metrics — Performans metrikleri\n"
            "/queue — Kuyruk durumu\n\n"
            "📁 *Görev Yönetimi*\n"
            "/tasks — Son görevler listesi\n"
            "/tasks pending — Bekleyen görevler\n"
            "/tasks running — Çalışan görevler\n"
            "/task \\<id\\> — Görev detayı\n"
            "/newtask — Yeni görev oluştur\n\n"
            "🔧 *Self-Repair* (Faz 11)\n"
            "/incidents — Açık incident listesi\n"
            "/repair \\<id\\> — Repair job başlat\n"
            "/proposals — Onay bekleyen PR\'ler\n"
            "/approve <pr_id> — PR onayla\n"
            "/reject <pr_id> — PR reddet\n\n"
            "🤖 *Sistem*\n"
            "/agents — Aktif ajanlar\n"
            "/logs — Son sistem logları\n"
            "/errors — Son hatalar\n"
        )
        admin_part = ""
        return base + admin_part

    # ── /status ────────────────────────────────────────────
    async def cmd_status(self, tid: str, args: str) -> str:
        try:
            from core.context import orchestrator, heal_engine
            from packages.packages.observability.metrics import metrics
            from packages.orchestration.application.job_queue import job_queue

            snap = metrics.snapshot()
            c    = snap["computed"]
            q    = job_queue.stats()
            hs   = heal_engine.system_health_score()

            # Sağlık emoji
            if hs >= 0.8:
                health_emoji = "🟢"
            elif hs >= 0.5:
                health_emoji = "🟡"
            else:
                health_emoji = "🔴"

            msg = (
                f"📊 *Sistem Durumu*\n\n"
                f"{health_emoji} Sağlık Skoru: `{hs:.0%}`\n"
                f"⏱ Uptime: `{snap['uptime_hms']}`\n\n"
                f"📁 *Görevler*\n"
                f"• Toplam: `{c['total_projects']}`\n"
                f"• Başarı Oranı: `{c['project_success_rate_pct']}%`\n\n"
                f"🔄 *Kuyruk*\n"
                f"• Bekleyen: `{q.get('queue_size', 0)}`\n"
                f"• Çalışan: `{q.get('running', 0)}`\n"
                f"• Tamamlanan: `{q.get('done', 0)}`\n"
                f"• Hatalı: `{q.get('failed', 0)}`\n\n"
                f"🤖 *LLM*\n"
                f"• Toplam Çağrı: `{c['total_llm_calls']}`\n"
                f"• Başarı: `{c['llm_success_rate_pct']}%`\n"
                f"• Toplam Maliyet: `${c['total_cost_usd']:.4f}`\n"
            )
            
            # Inline Keyboard ekle
            reply_markup = {
                "inline_keyboard": [[
                    {"text": "🔄 Yenile", "callback_data": "refresh_status:now"},
                    {"text": "📈 Metrikler", "callback_data": "view_metrics:now"}
                ]]
            }
            return (msg, reply_markup)
        except Exception as e:
            return f"❌ Durum alınamadı: {e}"

    # ── /tasks ─────────────────────────────────────────────
    async def cmd_tasks(self, tid: str, args: str) -> str:
        status_filter = args.strip() or None
        try:
            from packages.persistence.session import AsyncSessionLocal
            from packages.persistence.repository import ProjectRepository
            async with AsyncSessionLocal() as db:
                projects = await ProjectRepository.list_recent(
                    db, limit=10, status=status_filter
                )
            if not projects:
                return "📭 Görev bulunamadı."

            status_emojis = {
                "pending": "⏳", "running": "🔄", "done": "✅",
                "failed": "❌", "cancelled": "🚫",
            }
            lines = ["📁 *Son Görevler*\n"]
            for p in projects:
                emoji = status_emojis.get(p.status, "❓")
                short_id = str(p.id)[:8]
                title = p.title[:40] + ("..." if len(p.title) > 40 else "")
                lines.append(f"{emoji} `{short_id}` — {title}")
                lines.append(f"   Durum: {p.status} | Öncelik: {p.priority}")
                if p.progress_pct:
                    lines.append(f"   İlerleme: {p.progress_pct}%")
                lines.append("")
            lines.append("Detay için: /task \\<id\\>")
            
            reply_markup = {
                "inline_keyboard": [[
                    {"text": "⏳ Bekleyenler", "callback_data": "tasks_filter:pending"},
                    {"text": "🔄 Çalışanlar", "callback_data": "tasks_filter:running"}
                ], [
                    {"text": "🔄 Listeyi Yenile", "callback_data": "tasks_filter:all"}
                ]]
            }
            return ("\n".join(lines), reply_markup)
        except Exception as e:
            # Fallback: in-memory
            try:
                from core.context import orchestrator
                tasks = orchestrator.list_tasks()[-10:]
                if not tasks:
                    return "📭 Görev yok."
                lines = ["📁 *Son Görevler (önbellek)*\n"]
                for t in tasks:
                    lines.append(f"• `{t.id[:8]}` — {t.title[:40]}")
                    lines.append(f"   Durum: {t.status}")
                return "\n".join(lines)
            except Exception:
                return f"❌ Görevler alınamadı: {e}"

    # ── /task <id> ─────────────────────────────────────────
    async def cmd_task(self, tid: str, args: str) -> str:
        task_id = args.strip()
        if not task_id:
            return "❓ Kullanım: /task \\<görev\\_id\\>"
        try:
            from packages.persistence.session import AsyncSessionLocal
            from packages.persistence.repository import ProjectRepository, SubTaskRepository, TaskLogRepository
            from sqlalchemy import select
            from packages.persistence.models import Project
            async with AsyncSessionLocal() as db:
                # Kısmi ID ile de çalışsın
                result = await packages.persistence.execute(
                    select(Project).where(
                        Project.id.cast(str).startswith(task_id) |
                        (Project.job_id == task_id)
                    ).limit(1)
                )
                p = result.scalar_one_or_none()
                if not p:
                    return f"❓ `{task_id}` ile başlayan görev bulunamadı."

                subtasks = await SubTaskRepository.get_by_project(db, p.id)
                logs = await TaskLogRepository.get_by_project(db, p.id, limit=5)

            status_emojis = {
                "pending": "⏳", "running": "🔄", "done": "✅",
                "failed": "❌", "cancelled": "🚫",
            }
            emoji = status_emojis.get(p.status, "❓")

            done_st = sum(1 for s in subtasks if s.status == "done")
            total_st = len(subtasks)
            cost = sum(s.cost_usd for s in subtasks)

            msg = (
                f"{emoji} *Görev Detayı*\n\n"
                f"📌 *Başlık:* {p.title}\n"
                f"🆔 *ID:* `{str(p.id)[:16]}`\n"
                f"📊 *Durum:* {p.status}\n"
                f"🎯 *Öncelik:* {p.priority}\n"
                f"📤 *Kaynak:* {p.source}\n"
                f"📈 *İlerleme:* {p.progress_pct}%\n"
                f"🤖 *Alt Görevler:* {done_st}/{total_st} tamamlandı\n"
                f"💰 *Maliyet:* ${cost:.4f}\n"
            )
            if p.created_at:
                msg += f"🕐 *Oluşturulma:* {p.created_at.strftime('%d.%m %H:%M')}\n"
            if p.deadline:
                msg += f"⏰ *Deadline:* {p.deadline.strftime('%d.%m.%Y')}\n"
            if p.tags:
                msg += f"🏷 *Etiketler:* {', '.join(p.tags)}\n"
            if p.error_detail:
                msg += f"\n❗ *Hata:* {p.error_detail[:200]}\n"
            if logs:
                msg += f"\n📝 *Son Loglar:*\n"
                for log in logs[:3]:
                    msg += f"• `{log.event}` — {log.message[:80]}\n"
            return msg
        except Exception as e:
            return f"❌ Görev detayı alınamadı: {e}"

    # ── /newtask ───────────────────────────────────────────
    async def cmd_newtask(self, tid: str, args: str) -> str:
        """
        Kullanım: /newtask Başlık | Açıklama | öncelik
        Örnek:   /newtask Auth servisi yaz | JWT refresh token ekle | high
        """
        if not args.strip():
            return (
                "📝 *Yeni Görev Oluştur*\n\n"
                "Kullanım:\n"
                "`/newtask <başlık> | <açıklama> | <öncelik>`\n\n"
                "Örnek:\n"
                "`/newtask Auth servisi | JWT refresh ekle | high`\n\n"
                "Öncelik: `critical` `high` `medium` `low`"
            )

        parts = [p.strip() for p in args.split("|")]
        title       = parts[0] if len(parts) > 0 else ""
        description = parts[1] if len(parts) > 1 else ""
        priority    = parts[2].lower() if len(parts) > 2 else "medium"

        if not title:
            return "❌ Görev başlığı gereklidir."

        valid_priorities = {"critical", "high", "medium", "low"}
        if priority not in valid_priorities:
            priority = "medium"

        try:
            job_id = str(uuid.uuid4())[:12]
            db_project_id = ""

            # DB'ye kaydet
            try:
                from packages.persistence.session import AsyncSessionLocal
                from packages.persistence.repository import ProjectRepository, TaskLogRepository
                async with AsyncSessionLocal() as db:
                    p = await ProjectRepository.create(
                        db, title, description,
                        job_id=job_id,
                        source="telegram",
                        priority=priority,
                    )
                    await TaskLogRepository.write(
                        db, p.id, "created",
                        f"Telegram üzerinden oluşturuldu (kullanıcı: {tid})",
                        agent_id="telegram",
                    )
                    await packages.persistence.commit()
                    db_project_id = str(p.id)
            except Exception:
                pass

            # Semantic routing logic (Automatic Agent Choice)
            task_name = "run_project"
            try:
                from core.task_routing import task_router
                task_name = await task_router.route_task(title, description)
            except Exception as e:
                logger.warning(f"Semantic routing failed in Telegram, falling back to run_project: {e}")

            # Job queue'ya ekle
            from packages.orchestration.application.job_queue import job_queue
            job = await job_queue.enqueue(
                task_name,
                project_id=job_id,
                title=title,
                description=description,
                db_project_id=db_project_id,
            )

            # Olay yayını
            from core.events import event_bus
            await event_bus.emit(
                "project.started",
                title=title, project_id=job_id,
                severity="info", agent_id="telegram",
                phase="project",
                message=f"Telegram'dan görev: {title}",
            )

            return (
                f"✅ *Görev Oluşturuldu!*\n\n"
                f"📌 *Başlık:* {title}\n"
                f"🎯 *Öncelik:* {priority}\n"
                f"🆔 *Job ID:* `{job.id}`\n"
                f"📊 *Durum:* kuyruğa alındı\n\n"
                f"Takip için: /task {job.id}"
            )
        except Exception as e:
            return f"❌ Görev oluşturulamadı: {e}"

    # ── /agents ────────────────────────────────────────────
    async def cmd_agents(self, tid: str, args: str) -> str:
        try:
            from core.context import orchestrator, heal_engine
            health = orchestrator.get_health()
            snapshots = heal_engine.agent_snapshots()
            snap_map = {s["agent_id"]: s for s in snapshots}

            agent_emojis = {
                "architect":   "🏛️",
                "backend_dev": "⚙️",
                "frontend_dev":"🎨",
                "qa_engineer": "🧪",
                "devops":      "🚀",
                "security":    "🔒",
                "data_eng":    "🗄️",
                "tech_writer": "📝",
            }
            state_emojis = {
                "healthy": "🟢", "degraded": "🟡",
                "recovering": "🔵", "critical": "🔴", "backup": "⚠️",
            }

            lines = [f"🤖 *Ajan Durumu* ({len(health)} ajan)\n"]
            for agent_id, h in health.items():
                emoji   = agent_emojis.get(agent_id, "🤖")
                snap    = snap_map.get(agent_id, {})
                state   = snap.get("state", "healthy")
                se      = state_emojis.get(state, "❓")
                # get_health() dict[str, float] döner — h doğrudan float
                score   = h if isinstance(h, float) else h.get("score", 1.0)
                success = snap.get("success_count", 0)
                failure = snap.get("fail_streak", 0)
                lines.append(
                    f"{emoji} *{agent_id}*\n"
                    f"   {se} {state} | Skor: {score:.0%} "
                    f"| ✅{success} ❌{failure}"
                )
            return "\n".join(lines)
        except Exception as e:
            return f"❌ Ajan bilgisi alınamadı: {e}"

    # ── /logs ──────────────────────────────────────────────
    async def cmd_logs(self, tid: str, args: str) -> str:
        try:
            from core.events import event_bus
            events = event_bus.recent(15)
            if not events:
                return "📭 Log bulunamadı."

            severity_emojis = {
                "info": "ℹ️", "warning": "⚠️",
                "critical": "🔴", "resolved": "✅",
            }
            lines = ["📝 *Son Sistem Logları*\n"]
            for e in events[-10:]:
                se   = severity_emojis.get(e.get("severity", "info"), "•")
                ts   = e.get("timestamp", "")[:16].replace("T", " ")
                msg  = e.get("message", e.get("type", ""))[:80]
                lines.append(f"{se} `{ts}` {msg}")
            return "\n".join(lines)
        except Exception as e:
            return f"❌ Loglar alınamadı: {e}"

    # ── /errors ────────────────────────────────────────────
    async def cmd_errors(self, tid: str, args: str) -> str:
        try:
            from packages.persistence.session import AsyncSessionLocal
            from packages.persistence.repository import ProjectRepository
            async with AsyncSessionLocal() as db:
                failed = await ProjectRepository.list_recent(db, limit=10, status="failed")

            if not failed:
                return "✅ Hatalı görev yok."

            lines = [f"❌ *Hatalı Görevler* ({len(failed)} adet)\n"]
            for p in failed:
                short_id = str(p.id)[:8]
                lines.append(f"• `{short_id}` — {p.title[:50]}")
                if p.error_detail:
                    lines.append(f"  ↳ {p.error_detail[:100]}")
                if p.completed_at:
                    lines.append(f"  ↳ {p.completed_at.strftime('%d.%m %H:%M')}")
            return "\n".join(lines)
        except Exception as e:
            return f"❌ Hata bilgisi alınamadı: {e}"

    # ── /queue ─────────────────────────────────────────────
    async def cmd_queue(self, tid: str, args: str) -> str:
        try:
            from packages.orchestration.application.job_queue import job_queue
            stats = job_queue.stats()
            jobs  = job_queue.list_jobs(10)

            lines = [
                "🔄 *Kuyruk Durumu*\n",
                f"📊 Toplam: `{stats.get('total', 0)}`",
                f"⏳ Bekleyen: `{stats.get('queue_size', 0)}`",
                f"🔄 Çalışan: `{stats.get('running', 0)}`",
                f"✅ Tamamlanan: `{stats.get('done', 0)}`",
                f"❌ Hatalı: `{stats.get('failed', 0)}`",
                f"💀 Dead-letter: `{stats.get('dead_letter', 0)}`\n",
            ]

            running = [j for j in jobs if j.status.value == "running"]
            if running:
                lines.append("*Şu an çalışan:*")
                for j in running:
                    payload_title = j.payload.get("title", j.type)[:40]
                    lines.append(f"• `{j.id}` — {payload_title}")

            return "\n".join(lines)
        except Exception as e:
            return f"❌ Kuyruk bilgisi alınamadı: {e}"

    # ── /metrics ───────────────────────────────────────────
    async def cmd_metrics(self, tid: str, args: str) -> str:
        try:
            from packages.packages.observability.metrics import metrics
            snap = metrics.snapshot()
            c    = snap["computed"]
            lat  = snap.get("latencies", {})

            proj_lat = lat.get("projects.duration", {})
            llm_lat  = {}
            for provider in ("openai", "anthropic", "gemini"):
                key = f"packages.llm_gateway.{provider}.latency"
                if key in lat:
                    llm_lat[provider] = lat[key]

            msg = (
                f"📈 *Performans Metrikleri*\n\n"
                f"⏱ Uptime: `{snap['uptime_hms']}`\n\n"
                f"📁 *Projeler*\n"
                f"• Toplam: `{c['total_projects']}`\n"
                f"• Başarı: `{c['project_success_rate_pct']}%`\n"
            )
            if proj_lat:
                msg += (
                    f"• Ort. Süre: `{proj_lat.get('avg_s', 0):.1f}s`\n"
                    f"• P95: `{proj_lat.get('p95_s', 0):.1f}s`\n"
                )
            msg += (
                f"\n🤖 *LLM*\n"
                f"• Toplam: `{c['total_llm_calls']}`\n"
                f"• Başarı: `{c['llm_success_rate_pct']}%`\n"
                f"• Maliyet: `${c['total_cost_usd']:.4f}`\n"
                f"\n🔧 *Heal Engine*\n"
                f"• Başarı: `{c['heal_success_rate_pct']}%`\n"
            )
            for provider, lat_data in llm_lat.items():
                msg += f"\n*{provider}:* avg `{lat_data.get('avg_s',0):.2f}s` p95 `{lat_data.get('p95_s',0):.2f}s`"
            return msg
        except Exception as e:
            return f"❌ Metrikler alınamadı: {e}"

    # ── /authorize <id> (admin) ─────────────────────────────
    async def cmd_authorize(self, tid: str, args: str) -> str:
        if not await _is_admin(tid):
            return "❌ Bu komut sadece adminlere açıktır."
        target_id = args.strip()
        if not target_id:
            return "Kullanım: /authorize <telegram_id>"
        try:
            from packages.persistence.session import AsyncSessionLocal
            from packages.persistence.repository import TelegramRepository
            async with AsyncSessionLocal() as db:
                result = await TelegramRepository.authorize(db, target_id)
                await packages.persistence.commit()
            if result:
                return f"✅ `{target_id}` yetkilendirildi."
            else:
                return f"❓ `{target_id}` sistemde bulunamadı. Önce kullanıcının /start göndermesi gerekiyor."
        except Exception as e:
            return f"❌ Hata: {e}"

    # ── /users (admin) ─────────────────────────────────────
    async def cmd_users(self, tid: str, args: str) -> str:
        if not await _is_admin(tid):
            return "❌ Admin yetkisi gerekli."
        try:
            from packages.persistence.session import AsyncSessionLocal
            from packages.persistence.repository import TelegramRepository
            async with AsyncSessionLocal() as db:
                users = await TelegramRepository.list_users(db)
            lines = [f"👥 *Telegram Kullanıcıları* ({len(users)})\n"]
            for u in users:
                status = "✅ Yetkili" if u.is_authorized else "⛔ Yetkisiz"
                admin  = " 👑 Admin" if u.is_admin else ""
                name   = u.full_name or u.username or "—"
                lines.append(
                    f"• `{u.telegram_id}` — {name}\n"
                    f"  {status}{admin} | {u.command_count} komut"
                )
            return "\n".join(lines)
        except Exception as e:
            return f"❌ Hata: {e}"


    async def cmd_incidents(self, tid: str, args: str) -> str:
        """Açık incident'leri listele."""
        if not await _is_authorized(tid):
            return "⛔ Yetki gerekiyor"
        try:
            from packages.repair_engine.packages.memory.incident_memory import incident_memory
            open_incidents = [i for i in incident_memory.get_open()][:10]
            if not open_incidents:
                return "✅ Açık incident yok."
            lines = ["🚨 *Açık Incident'ler*\n"]
            for inc in open_incidents:
                lines.append(
                    f"• `{inc.incident_id[:12]}` — {inc.module} "
                    f"[{inc.severity.value.upper()}]\n  {inc.symptom[:80]}"
                )
            return "\n".join(lines)
        except Exception as e:
            return f"❌ Hata: {e}"

    async def cmd_repair(self, tid: str, args: str) -> str:
        """Repair job başlat: /repair <incident_id>"""
        if not await _is_authorized(tid):
            return "⛔ Yetki gerekiyor"
        incident_id = args.strip()
        if not incident_id:
            return "Kullanım: /repair <incident_id>"
        try:
            from packages.repair_engine.packages.memory.incident_memory import incident_memory
            from core.repair_orchestrator import get_repair_orchestrator
            import os
            incident = incident_memory.get(incident_id)
            if not incident:
                return f"❌ Incident bulunamadı: `{incident_id}`"
            orchestrator = get_repair_orchestrator(os.getcwd())
            job = await orchestrator.run(incident)
            return (
                f"⚙️ Repair job başlatıldı\n"
                f"Job ID: `{job.job_id}`\n"
                f"Durum: `{job.status.value}`"
            )
        except Exception as e:
            return f"❌ Hata: {e}"

    async def cmd_approvals(self, tid: str, args: str) -> str:
        """Onay bekleyen genel görev taleplerini listele."""
        if not await _is_authorized(tid):
            return "⛔ Yetki gerekiyor"
        try:
            from packages.quality_assurance.approval_gate import approval_gate
            pending = approval_gate.pending_requests()
            if not pending:
                return "✅ Onay bekleyen genel görev yok."
            lines = ["🎟️ *Onay Bekleyen Görevler*\n"]
            for r in pending[:5]:
                lines.append(
                    f"• `{r.id[:8]}` — *{r.operation}*\n"
                    f"  _{r.description[:60]}_ (Risk: {r.risk_level})"
                )
            lines.append("\nOnaylamak için: `/approve <id>`")
            return "\n".join(lines)
        except Exception as e:
            return f"❌ Hata: {e}"

    async def cmd_proposals(self, tid: str, args: str) -> str:
        """Onay bekleyen PR önerilerini listele."""
        if not await _is_authorized(tid):
            return "⛔ Yetki gerekiyor"
        try:
            from packages.repair_engine.release.pr_creator import get_pr_creator
            import os
            creator = get_pr_creator(os.getcwd())
            proposals = creator.list_proposals()
            pending = [p for p in proposals if p.get("status") == "awaiting_approval"]
            if not pending:
                return "✅ Onay bekleyen proposal yok."
            lines = ["📋 *Onay Bekleyen PR Önerileri*\n"]
            for p in pending[:5]:
                risk = p.get("risk_level", "?")
                emoji = "🔴" if risk == "high" else ("🟡" if risk == "medium" else "🟢")
                lines.append(
                    f"{emoji} `{p.get('pr_id','')[:12]}` — {p.get('title','')[:60]}"
                )
            lines.append("\nOnaylamak için: /approve <pr_id>")
            return "\n".join(lines)
        except Exception as e:
            return f"❌ Hata: {e}"

    async def cmd_approve(self, tid: str, args: str) -> str:
        """Onayla: /approve <id> (Hem PR hem Genel Görevler için)"""
        if not await _is_authorized(tid):
            return "⛔ Yetki gerekiyor"
        req_id = args.strip()
        if not req_id:
            return "Kullanım: /approve <id>"
        
        # 1. Önce genel onay kapısını dene
        try:
            from packages.quality_assurance.approval_gate import approval_gate
            req = approval_gate.decide(req_id, True, decided_by=f"telegram:{tid}")
            if req:
                from core.events import event_bus
                await event_bus.emit(
                    "approval.decided",
                    request_id=req_id,
                    approve=True,
                    severity="resolved",
                    agent_id=f"telegram:{tid}",
                    phase="approval",
                    message=f"Telegram üzerinden onay verildi: {req.operation}",
                )
                return f"✅ Görev onayı `{req_id[:8]}` verildi."
        except Exception:
            pass

        # 2. PR önerisini dene
        try:
            from api.repair_router import _persist_proposal_decision, _update_job_on_proposal_decision
            await _persist_proposal_decision(req_id, "approved", f"telegram:{tid}")
            await _update_job_on_proposal_decision(req_id, "approved", f"telegram:{tid}")
            return f"✅ PR `{req_id[:14]}` onaylandı."
        except Exception:
            pass
            
        return f"❌ `{req_id}` için bekleyen bir onay talebi bulunamadı."

    async def cmd_reject(self, tid: str, args: str) -> str:
        """Reddet: /reject <id> [neden]"""
        if not await _is_authorized(tid):
            return "⛔ Yetki gerekiyor"
        parts = args.split(None, 1)
        if not parts:
            return "Kullanım: /reject <id> [neden]"
        req_id = parts[0]
        reason = parts[1] if len(parts) > 1 else "User rejected via Telegram"

        # 1. Genel onay kapısı
        try:
            from packages.quality_assurance.approval_gate import approval_gate
            req = approval_gate.decide(req_id, False, decided_by=f"telegram:{tid}", reason=reason)
            if req:
                from core.events import event_bus
                await event_bus.emit(
                    "approval.decided",
                    request_id=req_id,
                    approve=False,
                    severity="warning",
                    agent_id=f"telegram:{tid}",
                    phase="approval",
                    message=f"Telegram üzerinden reddedildi: {req.operation}. Neden: {reason}",
                )
                return f"❌ Görev talebi `{req_id[:8]}` reddedildi."
        except Exception:
            pass

        # 2. PR önerisi
        try:
            from api.repair_router import _persist_proposal_decision, _update_job_on_proposal_decision
            await _persist_proposal_decision(req_id, "rejected", f"telegram:{tid}")
            await _update_job_on_proposal_decision(req_id, "rejected", f"telegram:{tid}")
            return f"❌ PR `{req_id[:14]}` reddedildi.{' Neden: ' + reason if reason else ''}"
        except Exception:
            pass

        return f"❌ `{req_id}` için bekleyen bir onay talebi bulunamadı."


    # ── /audit (ECC Repository Validation) ──────────────────
    async def cmd_audit(self, tid: str, args: str) -> str:
        if not await _is_authorized(tid):
            return "⛔ Yetki yetersiz."
        
        try:
            import subprocess
            import os
            
            repo_path = os.getcwd()
            # everything-claude-code-main projesinde validator'ları çalıştır
            # package.json içindeki 'test' script'i validator'ları tetikliyor
            
            await telegram_notifier.send_to_chat(int(tid), "🔍 *ECC Repo Denetimi Başlatılıyor...*\nLütfen bekleyin.")
            
            process = subprocess.Popen(
                ["npm", "test"],
                cwd=repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                output = stdout[-500:] if stdout else ""
                return (
                    "✅ *Repo Denetimi Başarılı!*\n\n"
                    "Tüm validator'lar ve hook'lar başarıyla geçti.\n"
                    f"```\n{output}\n```"
                )
            else:
                output = (stderr[-500:] if stderr else "") + (stdout[-500:] if stdout else "")
                return (
                    "⚠️ *Repo Denetiminde Sorunlar Bulundu!*\n\n"
                    "Bazı testler veya validator'lar başarısız oldu.\n"
                    f"```\n{output}\n```"
                )
        except Exception as e:
            return f"❌ Denetim hatası: {e}"


# ════════════════════════════════════════════════════════
# Komut Yönlendirici
# ════════════════════════════════════════════════════════
_handler = BotCommandHandler()

async def handle_callback_query(update_data: dict) -> Optional[tuple[int, str]]:
    """Tıklanan butona göre işlem yap."""
    query = update_data.get("callback_query")
    if not query:
        return None

    from_user = query.get("from", {})
    tid = str(from_user.get("id", ""))
    chat_id = query.get("message", {}).get("chat", {}).get("id")
    callback_data = query.get("data", "")

    if not chat_id or not tid or not callback_data:
        return None

    # Yetki kontrolü
    if not await _is_authorized(tid):
        return (chat_id, "⛔ Yetki yetersiz.", None)

    # Callback formatı: "action:id"
    if ":" not in callback_data:
        return (chat_id, "❓ Geçersiz işlem.", None)

    action, target_id = callback_data.split(":", 1)
    
    response = ""
    reply_markup = None
    
    if action == "approve":
        response = await _handler.cmd_approve(tid, target_id)
    elif action == "reject":
        response = await _handler.cmd_reject(tid, target_id)
    elif action == "refresh_status":
        res = await _handler.cmd_status(tid, "")
        response, reply_markup = res if isinstance(res, tuple) else (res, None)
    elif action == "view_metrics":
        response = await _handler.cmd_metrics(tid, "")
    elif action == "tasks_filter":
        res = await _handler.cmd_tasks(tid, target_id if target_id != "all" else "")
        response, reply_markup = res if isinstance(res, tuple) else (res, None)
    else:
        response = "❓ Bilinmeyen işlem."

    return (chat_id, response, reply_markup)


async def _handle_natural_language(tid: str, chat_id: int, text: str) -> Optional[tuple[int, str, Optional[dict]]]:
    """Doğal dil mesajını analiz et ve gerekirse görev oluştur."""
    if not await _is_authorized(tid):
        return (chat_id, "⛔ Mesajınızı işlemek için yetkiniz yok.", None)

    try:
        # Önce kullanıcıya "anladığımı" belli et
        await telegram_notifier.send_to_chat(chat_id, "🤖 *Mesajınızı analiz ediyorum...*")
        
        # NLP Yönlendirme (Title ve slug çıkart)
        # Mevcut task_router sadece slug döner, ama biz başlığı da tahmin edebiliriz.
        from core.task_routing import task_router
        import asyncio
        try:
            task_name = await asyncio.wait_for(task_router.route_task(text[:50], text), timeout=5.0)
        except asyncio.TimeoutError:
            return (chat_id, "⚠️ Zeka motorundan yanıt gelmedi (Timeout). Görev atanırken varsayılan mod kullanıldı.", None)
        
        # Görev oluştur (Basitleştirilmiş)
        job_id = str(uuid.uuid4())[:12]
        
        # DB Kaydı
        from packages.persistence.session import AsyncSessionLocal
        from packages.persistence.repository import ProjectRepository, TaskLogRepository
        async with AsyncSessionLocal() as db:
            p = await ProjectRepository.create(
                db, 
                title=f"AI: {text[:40]}...", 
                description=text,
                job_id=job_id,
                source="telegram_nlp",
                priority="medium",
            )
            await TaskLogRepository.write(
                db, p.id, "created",
                f"Telegram NLP üzerinden oluşturuldu (mod: {task_name})",
                agent_id="telegram_nlp",
            )
            await packages.persistence.commit()
            db_project_id = str(p.id)

        # Kuyruğa ekle
        from packages.orchestration.application.job_queue import job_queue
        job = await job_queue.enqueue(
            task_name,
            project_id=job_id,
            title=f"AI: {text[:40]}...",
            description=text,
            db_project_id=db_project_id,
        )

        response = (
            f"🚀 *Yapay Zeka Yeni Görev Algıladı!*\n\n"
            f"📌 *Başlık:* AI: {text[:40]}...\n"
            f"📑 *Eylem:* `{task_name}`\n"
            f"🆔 *ID:* `{job.id}`\n\n"
            "Görev kuyruğa alındı ve yürütülüyor.\n"
            f"Takip için: /task {job.id}"
        )
        await _log_command(tid, "nlp_task", text, response)
        return (chat_id, response, None)
        
    except Exception as e:
        logger.error(f"NLP İşleme hatası: {e}")
        return (chat_id, "❌ Mesajınızı bir göreve dönüştüremedim. Lütfen /newtask komutunu deneyin.", None)


COMMANDS = {
    "/start":       (_handler.cmd_start,       False),
    "/help":        (_handler.cmd_help,        True),
    "/status":      (_handler.cmd_status,      True),
    "/tasks":       (_handler.cmd_tasks,       True),
    "/task":        (_handler.cmd_task,        True),
    "/newtask":     (_handler.cmd_newtask,     True),
    "/agents":      (_handler.cmd_agents,      True),
    "/logs":        (_handler.cmd_logs,        True),
    "/errors":      (_handler.cmd_errors,      True),
    "/queue":       (_handler.cmd_queue,       True),
    "/metrics":     (_handler.cmd_metrics,     True),
    "/authorize":   (_handler.cmd_authorize,   True),
    "/users":       (_handler.cmd_users,       True),
    # Faz 11 — Self-Repair komutları
    "/incidents":   (_handler.cmd_incidents,   True),
    "/repair":      (_handler.cmd_repair,      True),
    "/approvals":   (_handler.cmd_approvals,   True),
    "/proposals":   (_handler.cmd_proposals,   True),
    "/approve":     (_handler.cmd_approve,     True),
    "/reject":      (_handler.cmd_reject,      True),
    "/audit":       (_handler.cmd_audit,       True),
}


async def handle_update(update_data: dict) -> Optional[tuple[int, str, Optional[dict]]]:
    # Callback Query Kontrolü
    if "callback_query" in update_data:
        return await handle_callback_query(update_data)

    msg = update_data.get("message") or update_data.get("edited_message")

    if not msg:
        return None

    chat_id    = msg.get("chat", {}).get("id")
    text       = msg.get("text", "").strip()
    from_user  = msg.get("from", {})
    telegram_id = str(from_user.get("id", ""))
    username   = from_user.get("username", "")
    full_name  = f"{from_user.get('first_name', '')} {from_user.get('last_name', '')}".strip()

    if not chat_id or not text or not telegram_id:
        return None

    # Kullanıcıyı DB'ye kaydet / güncelle
    await _upsert_user(telegram_id, username, full_name)

    # Komutu parse et
    parts   = text.split(None, 1)
    command = parts[0].split("@")[0].lower()   # /command@botname -> /command
    args    = parts[1] if len(parts) > 1 else ""

    if command not in COMMANDS:
        # NLP Desteği: Komut değilse doğal dil olarak işle (NLP)
        if text and not text.startswith("/"):
            return await _handle_natural_language(telegram_id, chat_id, text)
            
        response = f"❓ Bilinmeyen komut: `{command}`\nKomut listesi için /help"
        await _log_command(telegram_id, command, args, response, success=False)
        return (chat_id, response, None)

    fn, auth_required = COMMANDS[command]

    if auth_required and not await _is_authorized(telegram_id):
        response = (
            "⛔ Bu komutu kullanmak için yetkiniz yok.\n"
            f"Erişim için yöneticiye Telegram ID'nizi (`{telegram_id}`) bildirin."
        )
        await _log_command(telegram_id, command, args, response, success=False)
        return (chat_id, response, None)

    try:
        res = await fn(telegram_id, args)
        if isinstance(res, tuple):
            response, reply_markup = res
        else:
            response, reply_markup = res, None
    except Exception as e:
        logger.error(f"Telegram komut hatası [{command}]: {e}", exc_info=True)
        response, reply_markup = f"❌ Komut işlenirken hata oluştu.\nLütfen tekrar deneyin.", None

    await _log_command(telegram_id, command, args, str(response))
    return (chat_id, response, reply_markup)


# ══════════════════════════════════════════════════════════
# Genel Bildirim Yardımcısı
# ══════════════════════════════════════════════════════════
# Sistem genelinde telegram bildirim göndermek için basit bir yardımcı
# fonksiyon.  Diğer modüller ``TelegramNotifier`` ile uğraşmadan
# doğrudan bu fonksiyonu çağırarak bir mesaj ve başlık yollayabilirler.
# Örneğin:
#     await send_notification("Yeni Görev", "Projeyi başlattım")

async def send_notification(title: str, message: str = "", severity: str = "info") -> None:
    """
    Telegram üzerinden basit bir bildirim gönderir.

    Bu fonksiyon, bir başlık ve opsiyonel mesaj alır ve tüm yetkili
    alıcılara gönderir.  Severity parametresi gelecekte ikon veya
    formatlama için kullanılabilir; şu anda mesajın başına bir emoji
    ekler.

    Args:
        title:    Bildirimin başlığı.
        message:  Detay mesaj (opsiyonel).
        severity: Bilginin önemi (info|warning|error).  Mesajın başına
                   uygun bir emoji eklenir.
    """
    # Harici importtan bağımsız olması için burada içe aktar.
    try:
        notifier = TelegramNotifier()  # type: ignore
        emojis = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
        }
        prefix = emojis.get(severity, "🔔")
        text = f"{prefix} *{title}*"
        if message:
            text += f"\n\n{message}"
        await notifier._send_to_all(text)
    except Exception as e:
        # Log, but never raise; notifications are best-effort
        logger.warning(f"send_notification failed: {e}")


# ════════════════════════════════════════════════════════
# Bildirim Gönderici
# ════════════════════════════════════════════════════════
class TelegramNotifier:
    """
    Sistem olaylarında yetkili kullanıcılara bildirim gönderir.
    main.py'de event_bus.on_any() ile bağlanır.
    """

    NOTIFY_EVENTS = {
        "project.completed":        "✅ Görev tamamlandı",
        "project.failed":           "❌ Görev başarısız",
        "heal.critical":            "🔴 Kritik ajan sorunu",
        "system.cascade_fail":      "🚨 Sistem kaskat hatası",
        "approval.needed":          "⏳ Onay bekleniyor",
        # Faz 11 — Self-Repair olayları
        "packages.repair_engine.incident_created":  "🚨 Yeni Incident",
        "packages.repair_engine.job_started":       "⚙️ Repair Job Başladı",
        "packages.repair_engine.proposal_ready":    "📋 PR Önerisi Hazır — İnsan Onayı Gerekiyor",
        "packages.repair_engine.proposal_approved": "✅ PR Onaylandı",
        "packages.repair_engine.proposal_rejected": "❌ PR Reddedildi",
        "packages.repair_engine.canary_failed":     "🐦 Canary Doğrulama Başarısız",
        "packages.repair_engine.duplicate_incident":"🔁 Tekrar Eden Incident",
        "packages.repair_engine.manual_escalation": "🔔 Manuel İnceleme Gerekiyor",
        "provider.quarantined":     "📉 Sağlayıcı Karantinaya Alındı",
        "provider.recovered":       "📈 Sağlayıcı İyileşti",
        "system.metabolism.pacing": "🐢 Metabolizma Yavaşlatıldı (ECO)",
        "system.metabolism.blackout": "🌑 Metabolik Kararma (Emergency)",
    }

    def __init__(self):
        self._bot_token = BOT_TOKEN
        self._recipients: list[str] = list(ADMIN_IDS) + list(ALLOWED_IDS)

    async def notify_event(self, event_type: str, payload: dict):
        title = self.NOTIFY_EVENTS.get(event_type)
        if not title:
            return

        msg = f"🔔 *{title}*\n\n"

        # Genel alanlar
        if payload.get("title"):
            msg += f"📌 {payload['title']}\n"
        if payload.get("message"):
            msg += f"💬 {payload['message'][:200]}\n"
        if payload.get("duration_s"):
            msg += f"⏱ Süre: {payload['duration_s']}s\n"

        # Repair-özel alanlar (Faz 11)
        if payload.get("incident_id"):
            msg += f"🆔 Incident: `{payload['incident_id'][:14]}`\n"
        if payload.get("module"):
            msg += f"📦 Modül: `{payload['module']}`\n"
        if payload.get("symptom"):
            msg += f"⚠️ Semptom: {str(payload['symptom'])[:150]}\n"
        if payload.get("severity"):
            msg += f"🎯 Önem: *{payload['severity'].upper()}*\n"
        if payload.get("job_id"):
            msg += f"⚙️ Job: `{payload['job_id'][:14]}`\n"
        if payload.get("pr_id"):
            msg += f"📋 PR: `{payload['pr_id'][:14]}`\n"
        if payload.get("risk"):
            emoji = "🔴" if payload["risk"] == "high" else ("🟡" if payload["risk"] == "medium" else "🟢")
            msg += f"{emoji} Risk: *{payload['risk'].upper()}*\n"
        if payload.get("validation_summary"):
            msg += f"🧪 Validation: {payload['validation_summary']}\n"
        if payload.get("feedback_code"):
            msg += f"📝 Neden: `{payload['feedback_code']}`\n"
        if payload.get("dashboard_url"):
            msg += f"\n🔗 [Dashboard]({payload['dashboard_url']})"

        # LLM Sağlayıcı alanları
        if payload.get("provider"):
            msg += f"🤖 Sağlayıcı: `{payload['provider']}`\n"
        if payload.get("reason"):
            msg += f"❗ Neden: {payload['reason'][:100]}\n"
        if payload.get("agent"):
            msg += f"🎭 Ajan: `{payload['agent']}`\n"
        if payload.get("energy"):
            msg += f"🔋 Enerji: `%{int(payload['energy'] * 100)}`\n"
        if payload.get("delay_s"):
            msg += f"⏳ Gecikme: `{payload['delay_s']}s`\n"
        if payload.get("mode"):
            msg += f"⚙️ Mod: *{payload['mode'].upper()}*\n"

        reply_markup = None
        
        # Onay butonu ekle
        request_id = payload.get("request_id") or payload.get("pr_id")
        if event_type in ("approval.needed", "packages.repair_engine.proposal_ready") and request_id:
            reply_markup = {
                "inline_keyboard": [[
                    {"text": "✅ Onayla", "callback_data": f"approve:{request_id}"},
                    {"text": "❌ Reddet", "callback_data": f"reject:{request_id}"}
                ]]
            }

        await self._send_to_all(msg, reply_markup=reply_markup)

    async def notify_repair_proposal(
        self,
        pr_id:      str,
        job_id:     str,
        module:     str,
        risk:       str,
        validation: str,
        symptom:    str = "",
    ) -> None:
        """PR önerisi hazır — onay bildirimi."""
        await self.notify_event("packages.repair_engine.proposal_ready", {
            "pr_id":               pr_id,
            "job_id":              job_id,
            "module":              module,
            "risk":                risk,
            "validation_summary":  validation,
            "symptom":             symptom,
        })

    async def notify_repeated_incident(
        self, incident_id: str, module: str, count: int, symptom: str = ""
    ) -> None:
        """Tekrarlayan incident bildirimi."""
        await self.notify_event("packages.repair_engine.duplicate_incident", {
            "incident_id": incident_id,
            "module":      module,
            "symptom":     symptom,
            "message":     f"{module} modülünde {count}. kez aynı hata — Manual escalation gerekebilir.",
        })

    async def _send_to_all(self, text: str, reply_markup: Optional[dict] = None):
        if not self._bot_token or not self._recipients:
            return
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5) as client:
                for chat_id in self._recipients:
                    try:
                        payload = {
                            "chat_id": chat_id,
                            "text": text,
                            "parse_mode": "Markdown",
                            "disable_web_page_preview": True,
                        }
                        if reply_markup:
                            payload["reply_markup"] = reply_markup
                            
                        await client.post(
                            f"https://api.telegram.org/bot{self._bot_token}/sendMessage",
                            json=payload,
                        )
                    except Exception:
                        pass
        except Exception as e:
            logger.warning(f"Telegram bildirim gönderilemedi: {e}")

    async def send_to_chat(self, chat_id: int, text: str, reply_markup: Optional[dict] = None):
        """Belirli bir chat'e mesaj gönder."""
        if not self._bot_token:
            return False
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10) as client:
                payload = {
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": True,
                }
                if reply_markup:
                    payload["reply_markup"] = reply_markup

                resp = await client.post(
                    f"https://api.telegram.org/bot{self._bot_token}/sendMessage",
                    json=payload,
                )
                return resp.status_code == 200
        except Exception as e:
            logger.warning(f"Telegram mesaj gönderilemedi: {e}")
            return False


# Singleton notifier
telegram_notifier = TelegramNotifier()
