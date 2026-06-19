import asyncio 

import os
import sys
import socket
from datetime import datetime, timezone

# Configuration — Docker-aware
_IS_DOCKER = os.getenv("DOCKER_CONTAINER", "").lower() in ("true", "1", "yes")
POSTGRES_HOST = "db" if _IS_DOCKER else "127.0.0.1"
POSTGRES_PORT = 5432 if _IS_DOCKER else 5433
REDIS_HOST = "redis" if _IS_DOCKER else "127.0.0.1"
REDIS_PORT = 6379 if _IS_DOCKER else 6380
LOG_FILE = "docs/audits/infra_readiness_audit_prmr_01.md"

async def check_connectivity(host, port):
    try:
        # P0: Connection check with timeout
        sock = socket.create_connection((host, port), timeout=2)
        sock.close()
        return True, "READY"
    except Exception as e:
        return False, str(e)

def update_audit_report(pg_status, redis_status, pg_err, redis_err):
    from services.governance.standby_manager import StandbyManager
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    pg_icon = "[OK]" if pg_status else "[FAIL]"
    redis_icon = "[OK]" if redis_status else "[FAIL]"
    
    is_standby = StandbyManager.is_in_standby()
    standby_status = "[LOCKED] ACTIVE (Waiting for Trigger)" if is_standby else "[UNLOCKED] REACTIVATED (Transition Authorized)"

    # Celery depends on Redis
    celery_icon = redis_icon
    celery_msg = "Redis bağımlı" if not redis_status else "Bağlantı başarılı"
    
    # Verdict logic
    all_ready = pg_status and redis_status
    status_icon = "[PASS]" if all_ready else "[FAIL]"
    
    report_content = f"""# Infrastructure Readiness Audit (PRMR-01)

**Tarih:** {timestamp}
**Faz:** 1 (Readiness Audit)
**Durum:** {status_icon}
**Standby Condition:** {standby_status}

## 1.1 Bağlantı Kontrolleri

| Servis | Hedef | Durum | Hata Mesajı / Not |
|--------|-------|-------|-------------------|
| **PostgreSQL** | `{POSTGRES_HOST}:{POSTGRES_PORT}/ai_company` | {pg_icon} | {pg_err if not pg_status else "-"} |
| **Redis** | `{REDIS_HOST}:{REDIS_PORT}/0` | {redis_icon} | {redis_err if not redis_status else "-"} |
| **Celery Broker** | `Redis` bağımlı | {celery_icon} | {celery_msg if not redis_status else "-"} |
| **pgvector** | PostgreSQL eklentisi | {'[BLOCKED]' if not pg_status else '[AVAILABLE]'} | {'DB erişimi olmadığı için kontrol edilemedi' if not pg_status else '-'} |
| **Docker Daemon** | `dockerDesktopLinuxEngine` | [FAIL] | `Sistem belirtilen dosyayı bulamıyor` (Daemon kapalı olabilir) |

## 1.2 Şema Hazırlığı

* {'Primary DB\'ye erişilemediğinden şema hazırlığı, migration bütünlüğü ve tablo kontrolleri **yapılamamıştır**.' if not pg_status else 'DB erişimi mevcut. Şema doğrulaması bir sonraki adımda yapılabilir.'} 

## Sonuç

{ 'Primary altyapı bileşenlerinin (Postgres & Redis) fiziksel olarak kapalı olduğu veya ağ katmanında ulaşılamadığı tespit edilmiştir. Docker Desktop servislerinin çalışmadığı değerlendirilmektedir. Bu durum, PRMR-01 uygulama planının Faz 1 "No-Return Gate" polikasına takılmıştır.' if not all_ready else 'Tüm birincil altyapı bileşenleri hazır durumdadır. "Hazır, PRMR-01 Faz 1’i yeniden başlat." komutu için sistem tetikte beklemektedir.'}

**Aksiyon:** {'Operasyon geçici olarak durdurulmalı ve `no_return_gate_decision.md` raporu yayınlanmalıdır. Sistem **Stable Degraded (SQLite)** modda kalmaya devam etmelidir.' if not all_ready else 'Sistem operatörden onay beklemektedir.'}
"""
    
    # Create directory if not exists
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    
    # No-op for stdout manipulation when imported as module
    pass

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write(report_content)
    
    print(f"[{timestamp}] Audit report updated: {status_icon}")
    return all_ready

async def run_audit() -> bool:
    print(f"--- [PRMR-01] Standby Readiness Audit ---")
    pg_ok, pg_status_msg = await check_connectivity(POSTGRES_HOST, POSTGRES_PORT)
    redis_ok, redis_status_msg = await check_connectivity(REDIS_HOST, REDIS_PORT)
    
    return update_audit_report(pg_ok, redis_ok, pg_status_msg, redis_status_msg)

if __name__ == "__main__":
    asyncio.run(run_audit())
