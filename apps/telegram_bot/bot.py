"""
Telegram Bot â€” Faz 4
â€¢ /start /help /status /tasks /task /newtask /agents /logs /errors /queue /metrics
â€¢ KullanÄ±cÄ± yetkilendirme (is_authorized DB kontrolÃ¼)
â€¢ Komut geÃ§miÅŸi loglama (TelegramCommandLog)
â€¢ Sistem bildirimleri (hata, tamamlama, kritik alarm)
â€¢ GÃ¶revler "telegram" source olarak iÅŸaretlenir
â€¢ python-telegram-bot kÃ¼tÃ¼phanesi kullanÄ±lÄ±r

Kurulum: pip install python-telegram-bot>=20.0
Env:      TELEGRAM_BOT_TOKEN=... TELEGRAM_ALLOWED_IDS=123456,789012
"""

import asyncio
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from packages.observability.logging import get_logger
from packages.orchestration.application.task_routing import task_router
from packages.orchestration.application.job_queue import job_queue
from packages.orchestration.domain.events import event_bus

logger = get_logger("telegram.bot")

# â”€â”€ Env yapÄ±landÄ±rma â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
BOT_TOKEN     = os.getenv("TELEGRAM_BOT_TOKEN", "")
# VirgÃ¼lle ayrÄ±lmÄ±ÅŸ Telegram ID whitelist (DB kontrolÃ¼ olmadan hÄ±zlÄ± eriÅŸim)
ALLOWED_IDS   = set(
    filter(None, os.getenv("TELEGRAM_ALLOWED_IDS", "").split(","))
)
ADMIN_IDS     = set(
    filter(None, os.getenv("TELEGRAM_ADMIN_IDS", "").split(","))
)

# â”€â”€ Lazy imports (telegram paket opsiyonel) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def _tg_available() -> bool:
    try:
        import telegram  # noqa
        return True
    except ImportError:
        return False


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# Yetkilendirme
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
async def _is_authorized(telegram_id: str) -> bool:
    """Ã–nce env whitelist, sonra DB kontrolÃ¼."""
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


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# Komut Ä°ÅŸleyicileri
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
class BotCommandHandler:
    """Her komut iÃ§in handler metodu."""

    # â”€â”€ /start â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    async def cmd_start(self, tid: str, args: str) -> str:
        auth = await _is_authorized(tid)
        if not auth:
            return (
                "ğŸ‘‹ *Otonom YazÄ±lÄ±m Åirketi Bot*\n\n"
                "Bu bot sadece yetkili kullanÄ±cÄ±lara aÃ§Ä±ktÄ±r.\n"
                f"EriÅŸim iÃ§in yÃ¶neticiye Telegram ID'nizi (`{tid}`) bildirin.\n\n"
                "EÄŸer yetkiniz varsa /help ile baÅŸlayabilirsiniz."
            )
        return (
            "ğŸ¢ *Otonom YazÄ±lÄ±m GeliÅŸtirme Åirketi*\n\n"
            "Merhaba! Sisteme baÄŸlÄ±sÄ±nÄ±z.\n\n"
            "KullanÄ±labilir komutlar iÃ§in /help yazÄ±n.\n"
            "Sistem durumu iÃ§in /status yazÄ±n."
        )

    # â”€â”€ /help â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    async def cmd_help(self, tid: str, args: str) -> str:
        is_admin = await _is_admin(tid)
        base = (
            "ğŸ“‹ *Komut Listesi*\n\n"
            "ğŸ“Š *Durum ve Ä°zleme*\n"
            "/status â€” Sistem genel durumu\n"
            "/metrics â€” Performans metrikleri\n"
            "/queue â€” Kuyruk durumu\n\n"
            "ğŸ“ *GÃ¶rev YÃ¶netimi*\n"
            "/tasks â€” Son gÃ¶revler listesi\n"
            "/tasks pending â€” Bekleyen gÃ¶revler\n"
            "/tasks running â€” Ã‡alÄ±ÅŸan gÃ¶revler\n"
            "/task \\<id\\> â€” GÃ¶rev detayÄ±\n"
            "/newtask â€” Yeni gÃ¶rev oluÅŸtur\n\n"
            "ğŸ”§ *Self-Repair* (Faz 11)\n"
            "/incidents â€” AÃ§Ä±k incident listesi\n"
            "/repair \\<id\\> â€” Repair job baÅŸlat\n"
            "/proposals â€” Onay bekleyen PR\'ler\n"
            "/approve <pr_id> â€” PR onayla\n"
            "/reject <pr_id> â€” PR reddet\n\n"
            "ğŸ¤– *Sistem*\n"
            "/agents â€” Aktif ajanlar\n"
            "/logs â€” Son sistem loglarÄ±\n"
            "/errors â€” Son hatalar\n"
        )
        admin_part = ""
        return base + admin_part

    # â”€â”€ /status â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    async def cmd_status(self, tid: str, args: str) -> str:
        try:
            from packages.orchestration.application.job_queue import job_queue
            from packages.orchestration.agi.cognitive.sovereign_cortex import sovereign_cortex as orchestrator

            snap = metrics.snapshot()
            c    = snap["computed"]
            q    = job_queue.stats()
            hs   = 0.9 # Fallback
            try:
                from packages.repair_engine.heal_engine import heal_engine
                hs = heal_engine.system_health_score()
            except: pass

            # SaÄŸlÄ±k emoji
            if hs >= 0.8:
                health_emoji = "ğŸŸ¢"
            elif hs >= 0.5:
                health_emoji = "ğŸŸ¡"
            else:
                health_emoji = "ğŸ”´"

            msg = (
                f"ğŸ“Š *Sistem Durumu*\n\n"
                f"{health_emoji} SaÄŸlÄ±k Skoru: `{hs:.0%}`\n"
                f"â± Uptime: `{snap['uptime_hms']}`\n\n"
                f"ğŸ“ *GÃ¶revler*\n"
                f"â€¢ Toplam: `{c['total_projects']}`\n"
                f"â€¢ BaÅŸarÄ± OranÄ±: `{c['project_success_rate_pct']}%`\n\n"
                f"ğŸ”„ *Kuyruk*\n"
                f"â€¢ Bekleyen: `{q.get('queue_size', 0)}`\n"
                f"â€¢ Ã‡alÄ±ÅŸan: `{q.get('running', 0)}`\n"
                f"â€¢ Tamamlanan: `{q.get('done', 0)}`\n"
                f"â€¢ HatalÄ±: `{q.get('failed', 0)}`\n\n"
                f"ğŸ¤– *LLM*\n"
                f"â€¢ Toplam Ã‡aÄŸrÄ±: `{c['total_llm_calls']}`\n"
                f"â€¢ BaÅŸarÄ±: `{c['llm_success_rate_pct']}%`\n"
                f"â€¢ Toplam Maliyet: `${c['total_cost_usd']:.4f}`\n"
            )
            
            # Inline Keyboard ekle
            reply_markup = {
                "inline_keyboard": [[
                    {"text": "ğŸ”„ Yenile", "callback_data": "refresh_status:now"},
                    {"text": "ğŸ“ˆ Metrikler", "callback_data": "view_metrics:now"}
                ]]
            }
            return (msg, reply_markup)
        except Exception as e:
            return f"âŒ Durum alÄ±namadÄ±: {e}"

    # â”€â”€ /tasks â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
                return "ğŸ“­ GÃ¶rev bulunamadÄ±."

            status_emojis = {
                "pending": "â³", "running": "ğŸ”„", "done": "âœ…",
                "failed": "âŒ", "cancelled": "ğŸš«",
            }
            lines = ["ğŸ“ *Son GÃ¶revler*\n"]
            for p in projects:
                emoji = status_emojis.get(p.status, "â“")
                short_id = str(p.id)[:8]
                title = p.title[:40] + ("..." if len(p.title) > 40 else "")
                lines.append(f"{emoji} `{short_id}` â€” {title}")
                lines.append(f"   Durum: {p.status} | Ã–ncelik: {p.priority}")
                if p.progress_pct:
                    lines.append(f"   Ä°lerleme: {p.progress_pct}%")
                lines.append("")
            lines.append("Detay iÃ§in: /task \\<id\\>")
            
            reply_markup = {
                "inline_keyboard": [[
                    {"text": "â³ Bekleyenler", "callback_data": "tasks_filter:pending"},
                    {"text": "ğŸ”„ Ã‡alÄ±ÅŸanlar", "callback_data": "tasks_filter:running"}
                ], [
                    {"text": "ğŸ”„ Listeyi Yenile", "callback_data": "tasks_filter:all"}
                ]]
            }
            return ("\n".join(lines), reply_markup)
        except Exception as e:
            # Fallback: in-memory
            try:
                from packages.orchestration.agi.cognitive.sovereign_cortex import sovereign_cortex as orchestrator
                tasks = orchestrator.list_tasks()[-10:]
                if not tasks:
                    return "ğŸ“­ GÃ¶rev yok."
                lines = ["ğŸ“ *Son GÃ¶revler (Ã¶nbellek)*\n"]
                for t in tasks:
                    lines.append(f"â€¢ `{t.id[:8]}` â€” {t.title[:40]}")
                    lines.append(f"   Durum: {t.status}")
                return "\n".join(lines)
            except Exception:
                return f"âŒ GÃ¶revler alÄ±namadÄ±: {e}"

    # â”€â”€ /task <id> â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    async def cmd_task(self, tid: str, args: str) -> str:
        task_id = args.strip()
        if not task_id:
            return "â“ KullanÄ±m: /task \\<gÃ¶rev\\_id\\>"
        try:
            from packages.persistence.session import AsyncSessionLocal
            from packages.persistence.repository import ProjectRepository, SubTaskRepository, TaskLogRepository
            from sqlalchemy import select
            from packages.persistence.models import Project
            async with AsyncSessionLocal() as db:
                # KÄ±smi ID ile de Ã§alÄ±ÅŸsÄ±n
                result = await db.execute(
                    select(Project).where(
                        Project.id.cast(str).startswith(task_id) |
                        (Project.job_id == task_id)
                    ).limit(1)
                )
                p = result.scalar_one_or_none()
                if not p:
                    return f"â“ `{task_id}` ile baÅŸlayan gÃ¶rev bulunamadÄ±."

                subtasks = await SubTaskRepository.get_by_project(db, p.id)
                logs = await TaskLogRepository.get_by_project(db, p.id, limit=5)

            status_emojis = {
                "pending": "â³", "running": "ğŸ”„", "done": "âœ…",
                "failed": "âŒ", "cancelled": "ğŸš«",
            }
            emoji = status_emojis.get(p.status, "â“")

            done_st = sum(1 for s in subtasks if s.status == "done")
            total_st = len(subtasks)
            cost = sum(s.cost_usd for s in subtasks)

            msg = (
                f"{emoji} *GÃ¶rev DetayÄ±*\n\n"
                f"ğŸ“Œ *BaÅŸlÄ±k:* {p.title}\n"
                f"ğŸ†” *ID:* `{str(p.id)[:16]}`\n"
                f"ğŸ“Š *Durum:* {p.status}\n"
                f"ğŸ¯ *Ã–ncelik:* {p.priority}\n"
                f"ğŸ“¤ *Kaynak:* {p.source}\n"
                f"ğŸ“ˆ *Ä°lerleme:* {p.progress_pct}%\n"
                f"ğŸ¤– *Alt GÃ¶revler:* {done_st}/{total_st} tamamlandÄ±\n"
                f"ğŸ’° *Maliyet:* ${cost:.4f}\n"
            )
            if p.created_at:
                msg += f"ğŸ• *OluÅŸturulma:* {p.created_at.strftime('%d.%m %H:%M')}\n"
            if p.deadline:
                msg += f"â° *Deadline:* {p.deadline.strftime('%d.%m.%Y')}\n"
            if p.tags:
                msg += f"ğŸ· *Etiketler:* {', '.join(p.tags)}\n"
            if p.error_detail:
                msg += f"\nâ— *Hata:* {p.error_detail[:200]}\n"
            if logs:
                msg += f"\nğŸ“ *Son Loglar:*\n"
                for log in logs[:3]:
                    msg += f"â€¢ `{log.event}` â€” {log.message[:80]}\n"
            return msg
        except Exception as e:
            return f"âŒ GÃ¶rev detayÄ± alÄ±namadÄ±: {e}"

    # â”€â”€ /newtask â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    async def cmd_newtask(self, tid: str, args: str) -> str:
        """
        KullanÄ±m: /newtask BaÅŸlÄ±k | AÃ§Ä±klama | Ã¶ncelik
        Ã–rnek:   /newtask Auth servisi yaz | JWT refresh token ekle | high
        """
        if not args.strip():
            return (
                "ğŸ“ *Yeni GÃ¶rev OluÅŸtur*\n\n"
                "KullanÄ±m:\n"
                "`/newtask <baÅŸlÄ±k> | <aÃ§Ä±klama> | <Ã¶ncelik>`\n\n"
                "Ã–rnek:\n"
                "`/newtask Auth servisi | JWT refresh ekle | high`\n\n"
                "Ã–ncelik: `critical` `high` `medium` `low`"
            )

        parts = [p.strip() for p in args.split("|")]
        title       = parts[0] if len(parts) > 0 else ""
        description = parts[1] if len(parts) > 1 else ""
        priority    = parts[2].lower() if len(parts) > 2 else "medium"

        if not title:
            return "âŒ GÃ¶rev baÅŸlÄ±ÄŸÄ± gereklidir."

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
                        f"Telegram Ã¼zerinden oluÅŸturuldu (kullanÄ±cÄ±: {tid})",
                        agent_id="telegram",
                    )
                    await db.commit()
                    db_project_id = str(p.id)
            except Exception:
                pass

            # Semantic routing logic (Automatic Agent Choice)
            task_name = "run_project"
            try:
                from packages.orchestration.application.task_routing import task_router
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

            # Olay yayÄ±nÄ±
            from packages.orchestration.domain.events import event_bus
            await event_bus.emit(
                "project.started",
                title=title, project_id=job_id,
                severity="info", agent_id="telegram",
                phase="project",
                message=f"Telegram'dan gÃ¶rev: {title}",
            )

            return (
                f"âœ… *GÃ¶rev OluÅŸturuldu!*\n\n"
                f"ğŸ“Œ *BaÅŸlÄ±k:* {title}\n"
                f"ğŸ¯ *Ã–ncelik:* {priority}\n"
                f"ğŸ†” *Job ID:* `{job.id}`\n"
                f"ğŸ“Š *Durum:* kuyruÄŸa alÄ±ndÄ±\n\n"
                f"Takip iÃ§in: /task {job.id}"
            )
        except Exception as e:
            return f"âŒ GÃ¶rev oluÅŸturulamadÄ±: {e}"

    # â”€â”€ /agents â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    async def cmd_agents(self, tid: str, args: str) -> str:
        try:
            from packages.orchestration.agi.cognitive.sovereign_cortex import sovereign_cortex as orchestrator
            from packages.repair_engine.heal_engine import heal_engine
            health = orchestrator.get_health()
            snapshots = heal_engine.agent_snapshots()
            snap_map = {s["agent_id"]: s for s in snapshots}

            agent_emojis = {
                "architect":   "ğŸ›ï¸",
                "backend_dev": "âš™ï¸",
                "frontend_dev":"ğŸ¨",
                "qa_engineer": "ğŸ§ª",
                "devops":      "ğŸš€",
                "security":    "ğŸ”’",
                "data_eng":    "ğŸ—„ï¸",
                "tech_writer": "ğŸ“",
            }
            state_emojis = {
                "healthy": "ğŸŸ¢", "degraded": "ğŸŸ¡",
                "recovering": "ğŸ”µ", "critical": "ğŸ”´", "backup": "âš ï¸",
            }

            lines = [f"ğŸ¤– *Ajan Durumu* ({len(health)} ajan)\n"]
            for agent_id, h in health.items():
                emoji   = agent_emojis.get(agent_id, "ğŸ¤–")
                snap    = snap_map.get(agent_id, {})
                state   = snap.get("state", "healthy")
                se      = state_emojis.get(state, "â“")
                # get_health() dict[str, float] dÃ¶ner â€” h doÄŸrudan float
                score   = h if isinstance(h, float) else h.get("score", 1.0)
                success = snap.get("success_count", 0)
                failure = snap.get("fail_streak", 0)
                lines.append(
                    f"{emoji} *{agent_id}*\n"
                    f"   {se} {state} | Skor: {score:.0%} "
                    f"| âœ…{success} âŒ{failure}"
                )
            return "\n".join(lines)
        except Exception as e:
            return f"âŒ Ajan bilgisi alÄ±namadÄ±: {e}"

    # â”€â”€ /logs â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    async def cmd_logs(self, tid: str, args: str) -> str:
        try:
            from packages.orchestration.domain.events import event_bus
            events = event_bus.recent(15)
            if not events:
                return "ğŸ“­ Log bulunamadÄ±."

            severity_emojis = {
                "info": "â„¹ï¸", "warning": "âš ï¸",
                "critical": "ğŸ”´", "resolved": "âœ…",
            }
            lines = ["ğŸ“ *Son Sistem LoglarÄ±*\n"]
            for e in events[-10:]:
                se   = severity_emojis.get(e.get("severity", "info"), "â€¢")
                ts   = e.get("timestamp", "")[:16].replace("T", " ")
                msg  = e.get("message", e.get("type", ""))[:80]
                lines.append(f"{se} `{ts}` {msg}")
            return "\n".join(lines)
        except Exception as e:
            return f"âŒ Loglar alÄ±namadÄ±: {e}"

    # â”€â”€ /errors â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    async def cmd_errors(self, tid: str, args: str) -> str:
        try:
            from packages.persistence.session import AsyncSessionLocal
            from packages.persistence.repository import ProjectRepository
            async with AsyncSessionLocal() as db:
                failed = await ProjectRepository.list_recent(db, limit=10, status="failed")

            if not failed:
                return "âœ… HatalÄ± gÃ¶rev yok."

            lines = [f"âŒ *HatalÄ± GÃ¶revler* ({len(failed)} adet)\n"]
            for p in failed:
                short_id = str(p.id)[:8]
                lines.append(f"â€¢ `{short_id}` â€” {p.title[:50]}")
                if p.error_detail:
                    lines.append(f"  â†³ {p.error_detail[:100]}")
                if p.completed_at:
                    lines.append(f"  â†³ {p.completed_at.strftime('%d.%m %H:%M')}")
            return "\n".join(lines)
        except Exception as e:
            return f"âŒ Hata bilgisi alÄ±namadÄ±: {e}"

    # â”€â”€ /queue â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    async def cmd_queue(self, tid: str, args: str) -> str:
        try:
            from packages.orchestration.application.job_queue import job_queue
            stats = job_queue.stats()
            jobs  = job_queue.list_jobs(10)

            lines = [
                "ğŸ”„ *Kuyruk Durumu*\n",
                f"ğŸ“Š Toplam: `{stats.get('total', 0)}`",
                f"â³ Bekleyen: `{stats.get('queue_size', 0)}`",
                f"ğŸ”„ Ã‡alÄ±ÅŸan: `{stats.get('running', 0)}`",
                f"âœ… Tamamlanan: `{stats.get('done', 0)}`",
                f"âŒ HatalÄ±: `{stats.get('failed', 0)}`",
                f"ğŸ’€ Dead-letter: `{stats.get('dead_letter', 0)}`\n",
            ]

            running = [j for j in jobs if j.status.value == "running"]
            if running:
                lines.append("*Åu an Ã§alÄ±ÅŸan:*")
                for j in running:
                    payload_title = j.payload.get("title", j.type)[:40]
                    lines.append(f"â€¢ `{j.id}` â€” {payload_title}")

            return "\n".join(lines)
        except Exception as e:
            return f"âŒ Kuyruk bilgisi alÄ±namadÄ±: {e}"

    # â”€â”€ /metrics â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    async def cmd_metrics(self, tid: str, args: str) -> str:
        try:
            from packages.observability.metrics import metrics
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
                f"ğŸ“ˆ *Performans Metrikleri*\n\n"
                f"â± Uptime: `{snap['uptime_hms']}`\n\n"
                f"ğŸ“ *Projeler*\n"
                f"â€¢ Toplam: `{c['total_projects']}`\n"
                f"â€¢ BaÅŸarÄ±: `{c['project_success_rate_pct']}%`\n"
            )
            if proj_lat:
                msg += (
                    f"â€¢ Ort. SÃ¼re: `{proj_lat.get('avg_s', 0):.1f}s`\n"
                    f"â€¢ P95: `{proj_lat.get('p95_s', 0):.1f}s`\n"
                )
            msg += (
                f"\nğŸ¤– *LLM*\n"
                f"â€¢ Toplam: `{c['total_llm_calls']}`\n"
                f"â€¢ BaÅŸarÄ±: `{c['llm_success_rate_pct']}%`\n"
                f"â€¢ Maliyet: `${c['total_cost_usd']:.4f}`\n"
                f"\nğŸ”§ *Heal Engine*\n"
                f"â€¢ BaÅŸarÄ±: `{c['heal_success_rate_pct']}%`\n"
            )
            for provider, lat_data in llm_lat.items():
                msg += f"\n*{provider}:* avg `{lat_data.get('avg_s',0):.2f}s` p95 `{lat_data.get('p95_s',0):.2f}s`"
            return msg
        except Exception as e:
            return f"âŒ Metrikler alÄ±namadÄ±: {e}"

    # â”€â”€ /authorize <id> (admin) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    async def cmd_authorize(self, tid: str, args: str) -> str:
        if not await _is_admin(tid):
            return "âŒ Bu komut sadece adminlere aÃ§Ä±ktÄ±r."
        target_id = args.strip()
        if not target_id:
            return "KullanÄ±m: /authorize <telegram_id>"
        try:
            from packages.persistence.session import AsyncSessionLocal
            from packages.persistence.repository import TelegramRepository
            async with AsyncSessionLocal() as db:
                result = await TelegramRepository.authorize(db, target_id)
                await db.commit()
            if result:
                return f"âœ… `{target_id}` yetkilendirildi."
            else:
                return f"â“ `{target_id}` sistemde bulunamadÄ±. Ã–nce kullanÄ±cÄ±nÄ±n /start gÃ¶ndermesi gerekiyor."
        except Exception as e:
            return f"âŒ Hata: {e}"

    # â”€â”€ /users (admin) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    async def cmd_users(self, tid: str, args: str) -> str:
        if not await _is_admin(tid):
            return "âŒ Admin yetkisi gerekli."
        try:
            from packages.persistence.session import AsyncSessionLocal
            from packages.persistence.repository import TelegramRepository
            async with AsyncSessionLocal() as db:
                users = await TelegramRepository.list_users(db)
            lines = [f"ğŸ‘¥ *Telegram KullanÄ±cÄ±larÄ±* ({len(users)})\n"]
            for u in users:
                status = "âœ… Yetkili" if u.is_authorized else "â›” Yetkisiz"
                admin  = " ğŸ‘‘ Admin" if u.is_admin else ""
                name   = u.full_name or u.username or "â€”"
                lines.append(
                    f"â€¢ `{u.telegram_id}` â€” {name}\n"
                    f"  {status}{admin} | {u.command_count} komut"
                )
            return "\n".join(lines)
        except Exception as e:
            return f"âŒ Hata: {e}"


    async def cmd_incidents(self, tid: str, args: str) -> str:
        """AÃ§Ä±k incident'leri listele."""
        if not await _is_authorized(tid):
            return "â›” Yetki gerekiyor"
        try:
            from packages.repair_engine.memory.incident_memory import incident_memory
            open_incidents = [i for i in incident_memory.get_open()][:10]
            if not open_incidents:
                return "âœ… AÃ§Ä±k incident yok."
            lines = ["ğŸš¨ *AÃ§Ä±k Incident'ler*\n"]
            for inc in open_incidents:
                lines.append(
                    f"â€¢ `{inc.incident_id[:12]}` â€” {inc.module} "
                    f"[{inc.severity.value.upper()}]\n  {inc.symptom[:80]}"
                )
            return "\n".join(lines)
        except Exception as e:
            return f"âŒ Hata: {e}"

    async def cmd_repair(self, tid: str, args: str) -> str:
        """Repair job baÅŸlat: /repair <incident_id>"""
        if not await _is_authorized(tid):
            return "â›” Yetki gerekiyor"
        incident_id = args.strip()
        if not incident_id:
            return "KullanÄ±m: /repair <incident_id>"
        try:
            from packages.repair_engine.memory.incident_memory import incident_memory
            from packages.repair_engine.application.orchestrator import get_repair_orchestrator
            import os
            incident = incident_memory.get(incident_id)
            if not incident:
                return f"âŒ Incident bulunamadÄ±: `{incident_id}`"
            orchestrator = get_repair_orchestrator(os.getcwd())
            job = await orchestrator.run(incident)
            return (
                f"âš™ï¸ Repair job baÅŸlatÄ±ldÄ±\n"
                f"Job ID: `{job.job_id}`\n"
                f"Durum: `{job.status.value}`"
            )
        except Exception as e:
            return f"âŒ Hata: {e}"

    async def cmd_approvals(self, tid: str, args: str) -> str:
        """Onay bekleyen genel gÃ¶rev taleplerini listele."""
        if not await _is_authorized(tid):
            return "â›” Yetki gerekiyor"
        try:
            from packages.quality_assurance.approval_gate import approval_gate
            pending = approval_gate.pending_requests()
            if not pending:
                return "âœ… Onay bekleyen genel gÃ¶rev yok."
            lines = ["ğŸŸï¸ *Onay Bekleyen GÃ¶revler*\n"]
            for r in pending[:5]:
                lines.append(
                    f"â€¢ `{r.id[:8]}` â€” *{r.operation}*\n"
                    f"  _{r.description[:60]}_ (Risk: {r.risk_level})"
                )
            lines.append("\nOnaylamak iÃ§in: `/approve <id>`")
            return "\n".join(lines)
        except Exception as e:
            return f"âŒ Hata: {e}"

    async def cmd_proposals(self, tid: str, args: str) -> str:
        """Onay bekleyen PR Ã¶nerilerini listele."""
        if not await _is_authorized(tid):
            return "â›” Yetki gerekiyor"
        try:
            from packages.repair_engine.release.pr_creator import get_pr_creator
            import os
            creator = get_pr_creator(os.getcwd())
            proposals = creator.list_proposals()
            pending = [p for p in proposals if p.get("status") == "awaiting_approval"]
            if not pending:
                return "âœ… Onay bekleyen proposal yok."
            lines = ["ğŸ“‹ *Onay Bekleyen PR Ã–nerileri*\n"]
            for p in pending[:5]:
                risk = p.get("risk_level", "?")
                emoji = "ğŸ”´" if risk == "high" else ("ğŸŸ¡" if risk == "medium" else "ğŸŸ¢")
                lines.append(
                    f"{emoji} `{p.get('pr_id','')[:12]}` â€” {p.get('title','')[:60]}"
                )
            lines.append("\nOnaylamak iÃ§in: /approve <pr_id>")
            return "\n".join(lines)
        except Exception as e:
            return f"âŒ Hata: {e}"

    async def cmd_approve(self, tid: str, args: str) -> str:
        """Onayla: /approve <id> (Hem PR hem Genel GÃ¶revler iÃ§in)"""
        if not await _is_authorized(tid):
            return "â›” Yetki gerekiyor"
        req_id = args.strip()
        if not req_id:
            return "KullanÄ±m: /approve <id>"
        
        # 1. Ã–nce genel onay kapÄ±sÄ±nÄ± dene
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
                    message=f"Telegram Ã¼zerinden onay verildi: {req.operation}",
                )
                return f"âœ… GÃ¶rev onayÄ± `{req_id[:8]}` verildi."
        except Exception:
            pass

        # 2. PR Ã¶nerisini dene
        try:
            from api.repair_router import _persist_proposal_decision, _update_job_on_proposal_decision
            await _persist_proposal_decision(req_id, "approved", f"telegram:{tid}")
            await _update_job_on_proposal_decision(req_id, "approved", f"telegram:{tid}")
            return f"âœ… PR `{req_id[:14]}` onaylandÄ±."
        except Exception:
            pass
            
        return f"âŒ `{req_id}` iÃ§in bekleyen bir onay talebi bulunamadÄ±."

    async def cmd_reject(self, tid: str, args: str) -> str:
        """Reddet: /reject <id> [neden]"""
        if not await _is_authorized(tid):
            return "â›” Yetki gerekiyor"
        parts = args.split(None, 1)
        if not parts:
            return "KullanÄ±m: /reject <id> [neden]"
        req_id = parts[0]
        reason = parts[1] if len(parts) > 1 else "User rejected via Telegram"

        # 1. Genel onay kapÄ±sÄ±
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
                    message=f"Telegram Ã¼zerinden reddedildi: {req.operation}. Neden: {reason}",
                )
                return f"âŒ GÃ¶rev talebi `{req_id[:8]}` reddedildi."
        except Exception:
            pass

        # 2. PR Ã¶nerisi
        try:
            from api.repair_router import _persist_proposal_decision, _update_job_on_proposal_decision
            await _persist_proposal_decision(req_id, "rejected", f"telegram:{tid}")
            await _update_job_on_proposal_decision(req_id, "rejected", f"telegram:{tid}")
            return f"âŒ PR `{req_id[:14]}` reddedildi.{' Neden: ' + reason if reason else ''}"
        except Exception:
            pass

        return f"âŒ `{req_id}` iÃ§in bekleyen bir onay talebi bulunamadÄ±."


    # â”€â”€ /audit (ECC Repository Validation) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    async def cmd_audit(self, tid: str, args: str) -> str:
        if not await _is_authorized(tid):
            return "â›” Yetki yetersiz."
        
        try:
            import subprocess
            import os
            
            repo_path = os.getcwd()
            # everything-claude-code-main projesinde validator'larÄ± Ã§alÄ±ÅŸtÄ±r
            # package.json iÃ§indeki 'test' script'i validator'larÄ± tetikliyor
            
            await telegram_notifier.send_to_chat(int(tid), "ğŸ” *ECC Repo Denetimi BaÅŸlatÄ±lÄ±yor...*\nLÃ¼tfen bekleyin.")
            
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
                    "âœ… *Repo Denetimi BaÅŸarÄ±lÄ±!*\n\n"
                    "TÃ¼m validator'lar ve hook'lar baÅŸarÄ±yla geÃ§ti.\n"
                    f"```\n{output}\n```"
                )
            else:
                output = (stderr[-500:] if stderr else "") + (stdout[-500:] if stdout else "")
                return (
                    "âš ï¸ *Repo Denetiminde Sorunlar Bulundu!*\n\n"
                    "BazÄ± testler veya validator'lar baÅŸarÄ±sÄ±z oldu.\n"
                    f"```\n{output}\n```"
                )
        except Exception as e:
            return f"âŒ Denetim hatasÄ±: {e}"


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# Komut YÃ¶nlendirici
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
_handler = BotCommandHandler()

async def handle_callback_query(update_data: dict) -> Optional[tuple[int, str]]:
    """TÄ±klanan butona gÃ¶re iÅŸlem yap."""
    query = update_data.get("callback_query")
    if not query:
        return None

    from_user = query.get("from", {})
    tid = str(from_user.get("id", ""))
    chat_id = query.get("message", {}).get("chat", {}).get("id")
    callback_data = query.get("data", "")

    if not chat_id or not tid or not callback_data:
        return None

    # Yetki kontrolÃ¼
    if not await _is_authorized(tid):
        return (chat_id, "â›” Yetki yetersiz.", None)

    # Callback formatÄ±: "action:id"
    if ":" not in callback_data:
        return (chat_id, "â“ GeÃ§ersiz iÅŸlem.", None)

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
        response = "â“ Bilinmeyen iÅŸlem."

    return (chat_id, response, reply_markup)


async def _handle_natural_language(tid: str, chat_id: int, text: str) -> Optional[tuple[int, str, Optional[dict]]]:
    """DoÄŸal dil mesajÄ±nÄ± analiz et ve gerekirse gÃ¶rev oluÅŸtur."""
    if not await _is_authorized(tid):
        return (chat_id, "â›” MesajÄ±nÄ±zÄ± iÅŸlemek iÃ§in yetkiniz yok.", None)

    try:
        # Ã–nce kullanÄ±cÄ±ya "anladÄ±ÄŸÄ±mÄ±" belli et
        await telegram_notifier.send_to_chat(chat_id, "ğŸ¤– *MesajÄ±nÄ±zÄ± analiz ediyorum...*")
        
        # NLP YÃ¶nlendirme (Title ve slug Ã§Ä±kart)
        # Mevcut task_router sadece slug dÃ¶ner, ama biz baÅŸlÄ±ÄŸÄ± da tahmin edebiliriz.
        from core.task_routing import task_router
        import asyncio
        try:
            task_name = await asyncio.wait_for(task_router.route_task(text[:50], text), timeout=5.0)
        except asyncio.TimeoutError:
            return (chat_id, "âš ï¸ Zeka motorundan yanÄ±t gelmedi (Timeout). GÃ¶rev atanÄ±rken varsayÄ±lan mod kullanÄ±ldÄ±.", None)
        
        # GÃ¶rev oluÅŸtur (BasitleÅŸtirilmiÅŸ)
        job_id = str(uuid.uuid4())[:12]
        
        # DB KaydÄ±
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
                f"Telegram NLP Ã¼zerinden oluÅŸturuldu (mod: {task_name})",
                agent_id="telegram_nlp",
            )
            await packages.persistence.commit()
            db_project_id = str(p.id)

        # KuyruÄŸa ekle
        from packages.orchestration.application.job_queue import job_queue
        job = await job_queue.enqueue(
            task_name,
            project_id=job_id,
            title=f"AI: {text[:40]}...",
            description=text,
            db_project_id=db_project_id,
        )

        response = (
            f"ğŸš€ *Yapay Zeka Yeni GÃ¶rev AlgÄ±ladÄ±!*\n\n"
            f"ğŸ“Œ *BaÅŸlÄ±k:* AI: {text[:40]}...\n"
            f"ğŸ“‘ *Eylem:* `{task_name}`\n"
            f"ğŸ†” *ID:* `{job.id}`\n\n"
            "GÃ¶rev kuyruÄŸa alÄ±ndÄ± ve yÃ¼rÃ¼tÃ¼lÃ¼yor.\n"
            f"Takip iÃ§in: /task {job.id}"
        )
        await _log_command(tid, "nlp_task", text, response)
        return (chat_id, response, None)
        
    except Exception as e:
        logger.error(f"NLP Ä°ÅŸleme hatasÄ±: {e}")
        return (chat_id, "âŒ MesajÄ±nÄ±zÄ± bir gÃ¶reve dÃ¶nÃ¼ÅŸtÃ¼remedim. LÃ¼tfen /newtask komutunu deneyin.", None)


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
    # Faz 11 â€” Self-Repair komutlarÄ±
    "/incidents":   (_handler.cmd_incidents,   True),
    "/repair":      (_handler.cmd_repair,      True),
    "/approvals":   (_handler.cmd_approvals,   True),
    "/proposals":   (_handler.cmd_proposals,   True),
    "/approve":     (_handler.cmd_approve,     True),
    "/reject":      (_handler.cmd_reject,      True),
    "/audit":       (_handler.cmd_audit,       True),
}


async def handle_update(update_data: dict) -> Optional[tuple[int, str, Optional[dict]]]:
    # Callback Query KontrolÃ¼
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

    # KullanÄ±cÄ±yÄ± DB'ye kaydet / gÃ¼ncelle
    await _upsert_user(telegram_id, username, full_name)

    # Komutu parse et
    parts   = text.split(None, 1)
    command = parts[0].split("@")[0].lower()   # /command@botname -> /command
    args    = parts[1] if len(parts) > 1 else ""

    if command not in COMMANDS:
        # NLP DesteÄŸi: Komut deÄŸilse doÄŸal dil olarak iÅŸle (NLP)
        if text and not text.startswith("/"):
            return await _handle_natural_language(telegram_id, chat_id, text)
            
        response = f"â“ Bilinmeyen komut: `{command}`\nKomut listesi iÃ§in /help"
        await _log_command(telegram_id, command, args, response, success=False)
        return (chat_id, response, None)

    fn, auth_required = COMMANDS[command]

    if auth_required and not await _is_authorized(telegram_id):
        response = (
            "â›” Bu komutu kullanmak iÃ§in yetkiniz yok.\n"
            f"EriÅŸim iÃ§in yÃ¶neticiye Telegram ID'nizi (`{telegram_id}`) bildirin."
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
        logger.error(f"Telegram komut hatasÄ± [{command}]: {e}", exc_info=True)
        response, reply_markup = f"âŒ Komut iÅŸlenirken hata oluÅŸtu.\nLÃ¼tfen tekrar deneyin.", None

    await _log_command(telegram_id, command, args, str(response))
    return (chat_id, response, reply_markup)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# Genel Bildirim YardÄ±mcÄ±sÄ±
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# Sistem genelinde telegram bildirim gÃ¶ndermek iÃ§in basit bir yardÄ±mcÄ±
# fonksiyon.  DiÄŸer modÃ¼ller ``TelegramNotifier`` ile uÄŸraÅŸmadan
# doÄŸrudan bu fonksiyonu Ã§aÄŸÄ±rarak bir mesaj ve baÅŸlÄ±k yollayabilirler.
# Ã–rneÄŸin:
#     await send_notification("Yeni GÃ¶rev", "Projeyi baÅŸlattÄ±m")

async def send_notification(title: str, message: str = "", severity: str = "info") -> None:
    """
    Telegram Ã¼zerinden basit bir bildirim gÃ¶nderir.

    Bu fonksiyon, bir baÅŸlÄ±k ve opsiyonel mesaj alÄ±r ve tÃ¼m yetkili
    alÄ±cÄ±lara gÃ¶nderir.  Severity parametresi gelecekte ikon veya
    formatlama iÃ§in kullanÄ±labilir; ÅŸu anda mesajÄ±n baÅŸÄ±na bir emoji
    ekler.

    Args:
        title:    Bildirimin baÅŸlÄ±ÄŸÄ±.
        message:  Detay mesaj (opsiyonel).
        severity: Bilginin Ã¶nemi (info|warning|error).  MesajÄ±n baÅŸÄ±na
                   uygun bir emoji eklenir.
    """
    # Harici importtan baÄŸÄ±msÄ±z olmasÄ± iÃ§in burada iÃ§e aktar.
    try:
        notifier = TelegramNotifier()  # type: ignore
        emojis = {
            "info": "â„¹ï¸",
            "warning": "âš ï¸",
            "error": "âŒ",
        }
        prefix = emojis.get(severity, "ğŸ””")
        text = f"{prefix} *{title}*"
        if message:
            text += f"\n\n{message}"
        await notifier._send_to_all(text)
    except Exception as e:
        # Log, but never raise; notifications are best-effort
        logger.warning(f"send_notification failed: {e}")


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# Bildirim GÃ¶nderici
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
class TelegramNotifier:
    """
    Sistem olaylarÄ±nda yetkili kullanÄ±cÄ±lara bildirim gÃ¶nderir.
    main.py'de event_bus.on_any() ile baÄŸlanÄ±r.
    """

    NOTIFY_EVENTS = {
        "project.completed":        "âœ… GÃ¶rev tamamlandÄ±",
        "project.failed":           "âŒ GÃ¶rev baÅŸarÄ±sÄ±z",
        "heal.critical":            "ğŸ”´ Kritik ajan sorunu",
        "system.cascade_fail":      "ğŸš¨ Sistem kaskat hatasÄ±",
        "approval.needed":          "â³ Onay bekleniyor",
        # Faz 11 â€” Self-Repair olaylarÄ±
        "packages.repair_engine.incident_created":  "ğŸš¨ Yeni Incident",
        "packages.repair_engine.job_started":       "âš™ï¸ Repair Job BaÅŸladÄ±",
        "packages.repair_engine.proposal_ready":    "ğŸ“‹ PR Ã–nerisi HazÄ±r â€” Ä°nsan OnayÄ± Gerekiyor",
        "packages.repair_engine.proposal_approved": "âœ… PR OnaylandÄ±",
        "packages.repair_engine.proposal_rejected": "âŒ PR Reddedildi",
        "packages.repair_engine.canary_failed":     "ğŸ¦ Canary DoÄŸrulama BaÅŸarÄ±sÄ±z",
        "packages.repair_engine.duplicate_incident":"ğŸ” Tekrar Eden Incident",
        "packages.repair_engine.manual_escalation": "ğŸ”” Manuel Ä°nceleme Gerekiyor",
        "provider.quarantined":     "ğŸ“‰ SaÄŸlayÄ±cÄ± Karantinaya AlÄ±ndÄ±",
        "provider.recovered":       "ğŸ“ˆ SaÄŸlayÄ±cÄ± Ä°yileÅŸti",
        "system.metabolism.pacing": "ğŸ¢ Metabolizma YavaÅŸlatÄ±ldÄ± (ECO)",
        "system.metabolism.blackout": "ğŸŒ‘ Metabolik Kararma (Emergency)",
    }

    def __init__(self):
        self._bot_token = BOT_TOKEN
        self._recipients: list[str] = list(ADMIN_IDS) + list(ALLOWED_IDS)

    async def notify_event(self, event_type: str, payload: dict):
        title = self.NOTIFY_EVENTS.get(event_type)
        if not title:
            return

        msg = f"ğŸ”” *{title}*\n\n"

        # Genel alanlar
        if payload.get("title"):
            msg += f"ğŸ“Œ {payload['title']}\n"
        if payload.get("message"):
            msg += f"ğŸ’¬ {payload['message'][:200]}\n"
        if payload.get("duration_s"):
            msg += f"â± SÃ¼re: {payload['duration_s']}s\n"

        # Repair-Ã¶zel alanlar (Faz 11)
        if payload.get("incident_id"):
            msg += f"ğŸ†” Incident: `{payload['incident_id'][:14]}`\n"
        if payload.get("module"):
            msg += f"ğŸ“¦ ModÃ¼l: `{payload['module']}`\n"
        if payload.get("symptom"):
            msg += f"âš ï¸ Semptom: {str(payload['symptom'])[:150]}\n"
        if payload.get("severity"):
            msg += f"ğŸ¯ Ã–nem: *{payload['severity'].upper()}*\n"
        if payload.get("job_id"):
            msg += f"âš™ï¸ Job: `{payload['job_id'][:14]}`\n"
        if payload.get("pr_id"):
            msg += f"ğŸ“‹ PR: `{payload['pr_id'][:14]}`\n"
        if payload.get("risk"):
            emoji = "ğŸ”´" if payload["risk"] == "high" else ("ğŸŸ¡" if payload["risk"] == "medium" else "ğŸŸ¢")
            msg += f"{emoji} Risk: *{payload['risk'].upper()}*\n"
        if payload.get("validation_summary"):
            msg += f"ğŸ§ª Validation: {payload['validation_summary']}\n"
        if payload.get("feedback_code"):
            msg += f"ğŸ“ Neden: `{payload['feedback_code']}`\n"
        if payload.get("dashboard_url"):
            msg += f"\nğŸ”— [Dashboard]({payload['dashboard_url']})"

        # LLM SaÄŸlayÄ±cÄ± alanlarÄ±
        if payload.get("provider"):
            msg += f"ğŸ¤– SaÄŸlayÄ±cÄ±: `{payload['provider']}`\n"
        if payload.get("reason"):
            msg += f"â— Neden: {payload['reason'][:100]}\n"
        if payload.get("agent"):
            msg += f"ğŸ­ Ajan: `{payload['agent']}`\n"
        if payload.get("energy"):
            msg += f"ğŸ”‹ Enerji: `%{int(payload['energy'] * 100)}`\n"
        if payload.get("delay_s"):
            msg += f"â³ Gecikme: `{payload['delay_s']}s`\n"
        if payload.get("mode"):
            msg += f"âš™ï¸ Mod: *{payload['mode'].upper()}*\n"

        reply_markup = None
        
        # Onay butonu ekle
        request_id = payload.get("request_id") or payload.get("pr_id")
        if event_type in ("approval.needed", "packages.repair_engine.proposal_ready") and request_id:
            reply_markup = {
                "inline_keyboard": [[
                    {"text": "âœ… Onayla", "callback_data": f"approve:{request_id}"},
                    {"text": "âŒ Reddet", "callback_data": f"reject:{request_id}"}
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
        """PR Ã¶nerisi hazÄ±r â€” onay bildirimi."""
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
            "message":     f"{module} modÃ¼lÃ¼nde {count}. kez aynÄ± hata â€” Manual escalation gerekebilir.",
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
            logger.warning(f"Telegram bildirim gÃ¶nderilemedi: {e}")

    async def send_to_chat(self, chat_id: int, text: str, reply_markup: Optional[dict] = None):
        """Belirli bir chat'e mesaj gÃ¶nder."""
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
            logger.warning(f"Telegram mesaj gÃ¶nderilemedi: {e}")
            return False


# Singleton notifier
telegram_notifier = TelegramNotifier()

