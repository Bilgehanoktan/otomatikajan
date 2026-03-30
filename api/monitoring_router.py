"""
Monitoring & Metrik API — Faz 4
• GET /monitoring/overview     — Genel sistem sağlık özeti
• GET /monitoring/api/stats    — Endpoint bazlı istatistik
• GET /monitoring/api/series   — Zaman serisi trafik
• GET /monitoring/api/slowest  — En yavaş endpointler
• GET /monitoring/llm          — LLM provider istatistik
• GET /monitoring/queue        — Queue yoğunluğu
• GET /monitoring/system       — CPU/RAM/disk
• GET /monitoring/agents       — Ajan sağlık metrikleri
• GET /monitoring/errors       — Son hatalar
• POST /monitoring/api/cleanup — Eski kayıtları temizle (admin)
"""

import os
import time
import psutil
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, Query

from auth.jwt_auth import get_current_user, require_admin
from observability.logging import get_logger

logger = get_logger("api.monitoring")
router = APIRouter(prefix="/monitoring", tags=["Monitoring"])

# ── Performance Optimization: System Metrics Cache ─────────
_SYS_CACHE: Dict[str, Any] = {"data": None, "timestamp": 0}
_SYS_CACHE_TTL = 3.0  # 3 saniye cache



# ════════════════════════════════════════════════════════
# OVERVIEW — Tek bakışta sistem durumu
# ════════════════════════════════════════════════════════
@router.get("/overview", summary="Sistem genel sağlık durumu")
async def monitoring_overview(current_user=Depends(get_current_user)):
    """Dashboard'un ana özet kartları için."""
    result: dict = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services":  {},
        "metrics":   {},
        "queue":     {},
        "agents":    {},
        "system":    {},
    }

    # ── Servis durumları ──────────────────────────────────
    services: Dict[str, Any] = {}

    # Orchestrator
    try:
        from core.context import orchestrator, heal_engine
        services["orchestrator"] = {
            "status": "online",
            "health_score": heal_engine.system_health_score() if hasattr(heal_engine, "system_health_score") else 1.0,
            "agent_count": orchestrator.agent_count() if hasattr(orchestrator, "agent_count") else len(getattr(orchestrator, "_agents", {})),
        }
    except Exception as e:
        services["orchestrator"] = {
            "status": "offline",
            "error": str(e),
        }

    # Queue summary orchestrator'dan bağımsız toplanmalı
    try:
        from core.job_queue import job_queue

        q_stats = job_queue.stats()
        q_stats["supports_cancel"] = getattr(job_queue, "supports_cancel", False)
        q_stats["supports_pause"] = getattr(job_queue, "supports_pause", False)
        q_stats["supports_resume"] = getattr(job_queue, "supports_resume", False)

        services["job_queue"] = {
            "status": "online",
            **q_stats,
        }
        result["queue"] = q_stats
    except Exception as e:
        services["job_queue"] = {
            "status": "offline",
            "error": str(e),
        }

    # DB & Pool Stats
    try:
        from db.session import AsyncSessionLocal, _get_engine
        from sqlalchemy import text
        
        # Connection check
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
        
        # Pool stats
        engine = _get_engine()
        pool = engine.pool
        pool_stats = {
            "size": pool.size(),
            "checkedout": pool.checkedout(),
            "overflow": pool.overflow() if hasattr(pool, 'overflow') else 0,
            "checkedin": pool.checkedin() if hasattr(pool, 'checkedin') else 0,
            "timeout": getattr(pool, '_timeout', 30)
        }
        
        services["database"] = {
            "status": "online",
            "pool": pool_stats
        }
    except Exception as e:
        services["database"] = {"status": "offline", "error": str(e)}

    # Redis
    try:
        from config import REDIS_URL
        r_url = os.getenv("REDIS_URL") or REDIS_URL
        if r_url:
            import redis.asyncio as aioredis
            r = aioredis.from_url(r_url, socket_timeout=1.0)
            await r.ping()
            await r.aclose()
            services["redis"] = {"status": "online"}
        else:
            services["redis"] = {"status": "not_configured"}
    except Exception as e:
        services["redis"] = {"status": "offline", "error": str(e)}

    result["services"] = services

    # ── Metrikler ─────────────────────────────────────────
    try:
        from observability.metrics import metrics
        snap = metrics.snapshot()
        result["metrics"] = {
            "uptime_hms":        snap["uptime_hms"],
            "uptime_s":          snap["uptime_s"],
            **snap["computed"],
            "llm_latencies":     {
                k: v for k, v in snap.get("latencies", {}).items()
                if k.startswith("llm.")
            },
        }
    except Exception as _e:
        from observability.logging import get_logger
        get_logger("monitoring").warning("İşlem hatası: %s", _e)
        pass

    # ── Ajan sağlığı ─────────────────────────────────────
    try:
        from core.context import orchestrator, heal_engine
        result["agents"] = {
            "count":        orchestrator.agent_count(),
            "system_score": heal_engine.system_health_score(),
            "snapshots":    heal_engine.agent_snapshots(),
        }
    except Exception as _e:
        from observability.logging import get_logger
        get_logger("monitoring").warning("İşlem hatası: %s", _e)
        pass

    # ── Sistem kaynakları ─────────────────────────────────
    result["system"] = _system_resources()

    # ── Sistem Bütünlüğü (Faz 12.1 Integrity Patch) ──────
    try:
        from core.context import orchestrator
        if hasattr(orchestrator, "repair_orch"):
            result["integrity"] = orchestrator.repair_orch.get_capability_status()
    except Exception:
        pass

    # ── Sentinel: Opsiyonel Servis Takibi (Faz 14.1) ──────
    result["optional_services"] = {
        "telegram_bot": _check_os_process("telegram_app/main.py"),
        "watchdog":     _check_os_process("memory/watchdog.py"),
        "scheduler":    _check_os_process("scripts/scheduler.py")
    }

    return result


def _check_os_process(script_name: str) -> str:
    """Belirli bir scriptin çalışıp çalışmadığını psutil ile kontrol eder."""
    try:
        for proc in psutil.process_iter(['cmdline']):
            try:
                cmd = proc.info.get('cmdline')
                if cmd and any(script_name in part for part in cmd):
                    return "online"
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception:
        pass
    return "offline"


# ════════════════════════════════════════════════════════
# API İSTATİSTİKLERİ
# ════════════════════════════════════════════════════════
@router.get("/api/stats", summary="Endpoint bazlı API istatistikleri")
async def api_stats(hours: int = Query(24, ge=1, le=168), current_user=Depends(get_current_user)):
    try:
        from db.session import AsyncSessionLocal
        from db.repository import ApiMetricRepository
        async with AsyncSessionLocal() as db:
            stats = await ApiMetricRepository.endpoint_stats(db, hours=hours)

        # Toplam özet
        total_requests = sum(s["total"] for s in stats)
        total_errors   = sum(s["errors"] for s in stats)
        avg_ms         = (
            sum(s["avg_ms"] * s["total"] for s in stats) / total_requests
            if total_requests else 0
        )

        return {
            "hours":          hours,
            "total_requests": total_requests,
            "total_errors":   total_errors,
            "error_rate_pct": float(round(total_errors / total_requests * 100, 1)) if total_requests else 0.0,
            "avg_response_ms":float(round(avg_ms, 1)),
            "endpoints":      stats,
        }
    except Exception as e:
        return {"error": str(e), "endpoints": [], "total_requests": 0}


@router.get("/api/series", summary="Zaman bazlı trafik serisi")
async def api_time_series(
    hours:          int = Query(6, ge=1, le=48),
    bucket_minutes: int = Query(5, ge=1, le=60),
    current_user=Depends(get_current_user),
):
    try:
        from db.session import AsyncSessionLocal
        from db.repository import ApiMetricRepository
        async with AsyncSessionLocal() as db:
            series = await ApiMetricRepository.time_series(
                db, hours=hours, bucket_minutes=bucket_minutes
            )
        return {"hours": hours, "bucket_minutes": bucket_minutes, "series": series}
    except Exception as e:
        return {"error": str(e), "series": []}


@router.get("/api/slowest", summary="En yavaş endpointler")
async def slowest_endpoints(hours: int = Query(24, ge=1, le=168), limit: int = Query(10), current_user=Depends(require_admin)):
    try:
        from db.session import AsyncSessionLocal
        from db.repository import ApiMetricRepository
        async with AsyncSessionLocal() as db:
            stats = await ApiMetricRepository.endpoint_stats(db, hours=hours)
        
        # Explicitly cast to list for type checkers
        sorted_by_latency = sorted(list(stats), key=lambda x: x.get("avg_ms", 0), reverse=True)
        return sorted_by_latency[:limit]
    except Exception as e:
        return {"error": str(e)}


# ════════════════════════════════════════════════════════
# LLM PROVIDER
# ════════════════════════════════════════════════════════
@router.get("/llm", summary="LLM provider istatistikleri")
async def llm_monitoring(current_user=Depends(get_current_user)):
    try:
        from core.context import orchestrator
        provider_stats = orchestrator.model_orch.provider_stats()
    except Exception:
        provider_stats = []

    try:
        from observability.metrics import metrics
        snap     = metrics.snapshot()
        counters = snap["counters"]
        latencies= snap["latencies"]
        computed = snap["computed"]

        providers_detail: Dict[str, Any] = {}
        for provider in ("openai", "anthropic", "gemini"):
            key_total   = f"llm.{provider}.calls.total"
            key_success = f"llm.{provider}.calls.success"
            key_fail    = f"llm.{provider}.calls.failure"
            key_tokens  = f"llm.{provider}.tokens"
            lat_key     = f"llm.{provider}.latency"

            total   = counters.get(key_total, 0)
            success = counters.get(key_success, 0)
            fail    = counters.get(key_fail, 0)
            tokens  = counters.get(key_tokens, 0)

            providers_detail[provider] = {
                "total":       total,
                "success":     success,
                "failure":     fail,
                "tokens":      tokens,
                "success_rate": round(success / total * 100, 1) if total else 0,
                "latency":     latencies.get(lat_key, {}).get("avg_s", 0),
                "p95_s":       latencies.get(lat_key, {}).get("p95_s", 0),
            }

        total_cost = computed.get("total_cost_usd", 0)
        return {
            "total_llm_calls": computed.get("total_llm_calls", 0),
            "total_cost_usd":  total_cost,
            "llm_success_rate": computed.get("llm_success_rate_pct", 0),
            "providers":        providers_detail,
            "circuit_status":   provider_stats,
        }
    except Exception as e:
        return {"error": str(e), "providers": {}, "circuit_status": provider_stats}


# ════════════════════════════════════════════════════════
# QUEUE
# ════════════════════════════════════════════════════════
@router.get("/queue", summary="Kuyruk yoğunluk metrikleri")
async def queue_monitoring(current_user=Depends(require_admin)):
    try:
        from core.job_queue import job_queue

        stats = job_queue.stats()
        jobs = job_queue.list_jobs(50)
        dead = job_queue.dead_letters

        recent_done = sum(
            1 for j in jobs
            if j.completed_at and getattr(j.status, "value", j.status) == "completed"
        )

        return {
            **stats,
            "backend":     getattr(job_queue, "backend_name", "unknown"),
            "supports_cancel": getattr(job_queue, "supports_cancel", False),
            "supports_pause": getattr(job_queue, "supports_pause", False),
            "supports_resume": getattr(job_queue, "supports_resume", False),
            "listing_scope": getattr(getattr(job_queue, "capabilities", None), "listing_scope", "unknown"),
            "done": stats.get("completed", 0),      # geçici alias
            "failed": stats.get("error", 0),        # geçici alias
            "throughput_last_hour": recent_done,
            "dead_letter_count": len(dead),
            "recent_jobs": [
                {
                    "id": j.id,
                    "type": j.type,
                    "status": getattr(j.status, "value", j.status),
                    "attempts": j.attempts,
                    "title": j.payload.get("title", j.type)[:50],
                    "created_at": j.created_at,
                    "started_at": j.started_at,
                    "completed_at": j.completed_at,
                }
                for j in jobs[-20:]
            ],
        }
    except Exception as e:
        return {"error": str(e)}



# ════════════════════════════════════════════════════════
# SYSTEM RESOURCES
# ════════════════════════════════════════════════════════
@router.get("/system", summary="Sistem kaynakları (CPU/RAM)")
async def system_resources(current_user=Depends(get_current_user)):
    return _system_resources()


def _system_resources() -> dict:
    """Sistem kaynaklarını getirir (Cache destekli & Disk IO detaylı)."""
    now = time.time()
    
    # ── Performance: Cache Check ────────────────────────
    if _SYS_CACHE["data"] and (now - _SYS_CACHE["timestamp"] < _SYS_CACHE_TTL):
        return _SYS_CACHE["data"]

    result = {"available": False}
    try:
        import psutil
        
        # CPU & Mem
        cpu   = psutil.cpu_percent(interval=None) # Non-blocking
        mem   = psutil.virtual_memory()
        
        # Disk Stats
        disk  = psutil.disk_usage("/")
        disk_io = psutil.disk_io_counters()
        
        # Net IO
        net_io = psutil.net_io_counters()

        result = {
            "available": True,
            "cpu_pct":   round(cpu, 1),
            "ram_total_gb":  round(mem.total / 1024**3, 1),
            "ram_used_gb":   round(mem.used  / 1024**3, 1),
            "ram_pct":       round(mem.percent, 1),
            "disk_total_gb": round(disk.total / 1024**3, 1),
            "disk_used_gb":  round(disk.used  / 1024**3, 1),
            "disk_pct":      round(disk.percent, 1),
            "io": {
                "read_mb":  round(disk_io.read_bytes / 1024**2, 1) if disk_io else 0,
                "write_mb": round(disk_io.write_bytes / 1024**2, 1) if disk_io else 0,
                "net_sent_mb": round(net_io.bytes_sent / 1024**2, 1) if net_io else 0,
                "net_recv_mb": round(net_io.bytes_recv / 1024**2, 1) if net_io else 0,
            },
            "boot_time": datetime.fromtimestamp(psutil.boot_time(), tz=timezone.utc).isoformat(),
            "cached_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Cache Update
        _SYS_CACHE["data"] = result
        _SYS_CACHE["timestamp"] = now

    except ImportError:
        result = {"available": False, "note": "psutil kurulu değil"}
    except Exception as e:
        result = {"available": False, "error": str(e)}
        
    return result



# ════════════════════════════════════════════════════════
# AGENTS MONITORING
# ════════════════════════════════════════════════════════
@router.get("/agents", summary="Ajan sağlık ve performans metrikleri")
async def agents_monitoring(current_user=Depends(get_current_user)):
    try:
        from core.context import orchestrator, heal_engine
        from observability.metrics import metrics

        snap     = metrics.snapshot()
        counters = snap["counters"]
        health   = orchestrator.get_health()
        snapshots= heal_engine.agent_snapshots()
        snap_map = {s["agent_id"]: s for s in snapshots}

        agents_data: Dict[str, Any] = {}
        for agent_id, h in health.items():
            s = snap_map.get(agent_id, {})
            # h bazen direkt float (health score) olabiliyor, bazen dict
            h_score = h if isinstance(h, (int, float)) else h.get("score", 1.0)
            
            agents_data[agent_id] = {
                "id":           agent_id,
                "state":        s.get("state", "healthy"),
                "health_score": h_score,
                "success":      h.get("success", 0) if isinstance(h, dict) else 0,
                "failure":      h.get("failure", 0) if isinstance(h, dict) else 0,
                "avg_latency":  h.get("avg_latency", 0) if isinstance(h, dict) else 0,
                "circuit":      s.get("circuit", "closed"),
                "recovery_count": s.get("recovery_count", 0),
            }

        return {
            "system_score":  heal_engine.system_health_score(),
            "agents":        agents_data,
            "recent_events": heal_engine.recent_events(20),
        }
    except Exception as e:
        return {"error": str(e), "agents": {}}


# ════════════════════════════════════════════════════════
# ERRORS
# ════════════════════════════════════════════════════════
@router.get("/errors", summary="Son hatalar ve kritik olaylar")
async def recent_errors(limit: int = Query(50, ge=1, le=200)):
    errors = []

    # 1. EventBus'tan kritik olaylar
    try:
        from core.events import event_bus
        all_events = event_bus.recent(200)
        for e in all_events:
            if e.get("severity") in ("critical", "warning"):
                errors.append({
                    "source":    "event_bus",
                    "type":      e.get("type"),
                    "message":   e.get("message", ""),
                    "severity":  e.get("severity"),
                    "agent_id":  e.get("agent_id"),
                    "timestamp": e.get("timestamp"),
                })
    except Exception as _e:
        from observability.logging import get_logger
        get_logger("monitoring").warning("İşlem hatası: %s", _e)
        pass

    # 2. In-memory metrik hataları
    try:
        from observability.metrics import metrics
        snap   = metrics.snapshot()
        for err_type, count in snap.get("errors", {}).items():
            errors.append({
                "source":  "metrics",
                "type":    err_type,
                "count":   count,
                "severity":"warning",
            })
    except Exception as _e:
        from observability.logging import get_logger
        get_logger("monitoring").warning("İşlem hatası: %s", _e)
        pass

    # 3. DB'den başarısız görevler
    try:
        from db.session import AsyncSessionLocal
        from db.repository import ProjectRepository
        from db.models import ProjectStatus
        async with AsyncSessionLocal() as db:
            failed = await ProjectRepository.list_recent(db, limit=20, status=ProjectStatus.ERROR.value)
        for p in failed:
            errors.append({
                "source":     "task",
                "type":       "task_failed",
                "task_id":    str(p.id),
                "title":      p.title,
                "message":    p.error_detail or "Bilinmeyen hata",
                "severity":   "critical",
                "timestamp":  p.completed_at.isoformat() if p.completed_at else None,
            })
    except Exception as _e:
        from observability.logging import get_logger
        get_logger("monitoring").warning("İşlem hatası: %s", _e)
        pass

    # Zaman sırasına göre sırala
    errors.sort(key=lambda x: str(x.get("timestamp") or ""), reverse=True)
    return list(errors)[:limit]


# ════════════════════════════════════════════════════════
# CLEANUP (admin)
# ════════════════════════════════════════════════════════
@router.post("/api/cleanup", summary="Eski API metrik kayıtlarını temizle", dependencies=[Depends(require_admin)])
async def cleanup_api_metrics(days: int = Query(7, ge=1, le=90)):
    try:
        from db.session import AsyncSessionLocal
        from db.repository import ApiMetricRepository
        async with AsyncSessionLocal() as db:
            deleted = await ApiMetricRepository.cleanup_old(db, days=days)
            await db.commit()
        return {"deleted": deleted, "older_than_days": days}
    except Exception as e:
        return {"error": str(e)}
